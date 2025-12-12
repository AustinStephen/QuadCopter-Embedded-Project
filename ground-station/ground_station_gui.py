"""Ground Station + PyQt GUI demo with artificial horizon and human-readable GPS."""

import sys
import socket
import re

# pylint: disable=no-member
import cv2
import numpy as np
import pynmea2

from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
)

########################
# GroundStation        #
########################

class GroundStation:
    """A class to represent a Ground Station for a quadcopter project."""
    def __init__(
        self,
        ipAddress="0.0.0.0",
        videoStreamURL="udp://0.0.0.0:5000",
        gpsPort=5001,
        imuPort=5002,
    ):
        """
        Initializes the GroundStation and ensure the sockets/URL match
        on the onboard system.
        """
        self.ipAddress = ipAddress
        self.videoStreamURL = videoStreamURL

        # IMU socket
        try:
            self.imuSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.imuSocket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)
            self.imuSocket.bind((self.ipAddress, imuPort))
            print(
                f"Listening for IMU UDP packets on {self.ipAddress}:{imuPort} (Ctrl+C to stop)"
            )
        except OSError as e:
            print(f"Failed to bind IMU UDP socket on {self.ipAddress}:{imuPort}: {e}")
            sys.exit(1)

        # GPS socket
        try:
            self.gpsSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.gpsSocket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)
            self.gpsSocket.bind((self.ipAddress, gpsPort))
            print(
                f"Listening for GPS UDP packets on {self.ipAddress}:{gpsPort} (Ctrl+C to stop)"
            )
        except OSError as e:
            print(f"Failed to bind GPS UDP socket on {self.ipAddress}:{gpsPort}: {e}")
            sys.exit(1)

    def __del__(self):
        """Destructor to close sockets to the quadcopter onboard brain."""
        try:
            self.imuSocket.close()
        except Exception:
            pass
        try:
            self.gpsSocket.close()
        except Exception:
            pass


########################
# Threads              #
########################

class VideoThread(QThread):
    frame_received = pyqtSignal(np.ndarray)

    def __init__(self, ground_station: GroundStation, parent=None):
        super().__init__(parent)
        self.gs = ground_station
        self._running = False

    def run(self):
        self._running = True
        cap = cv2.VideoCapture(self.gs.videoStreamURL, cv2.CAP_FFMPEG)

        if not cap.isOpened():
            print("Could not open UDP video stream")
            return

        while self._running:
            ret, frame = cap.read()
            if not ret:
                print("No frame received (stream might not be coming in)")
                break

            self.frame_received.emit(frame)

        cap.release()

    def stop(self):
        self._running = False
        self.wait()


class IMUThread(QThread):
    # emit raw line; main window parses to roll/pitch
    line_received = pyqtSignal(str)

    def __init__(self, ground_station: GroundStation, parent=None):
        super().__init__(parent)
        self.gs = ground_station
        self._running = False

    def run(self):
        self._running = True
        sock = self.gs.imuSocket

        while self._running:
            data, _ = sock.recvfrom(4096)
            text = data.decode("utf-8", errors="replace").strip()
            if text:
                self.line_received.emit(text)

    def stop(self):
        self._running = False
        self.wait()


class GPSThread(QThread):
    line_received = pyqtSignal(str)

    def __init__(self, ground_station: GroundStation, parent=None):
        super().__init__(parent)
        self.gs = ground_station
        self._running = False

    def run(self):
        self._running = True
        sock = self.gs.gpsSocket

        while self._running:
            data, _ = sock.recvfrom(4096)
            text = data.decode("utf-8", errors="replace").strip()
            if not text:
                continue

            # Some implementations might send multiple lines in one packet
            for line in text.splitlines():
                line = line.strip()
                if line:
                    self.line_received.emit(line)

    def stop(self):
        self._running = False
        self.wait()


########################
# Helpers              #
########################

def parse_imu_line_to_rpy(line: str):
    """
    Try to extract roll, pitch, yaw (in degrees) from an IMU text line.

    We just grab the first three numbers we see in the string.
    This makes it robust to formats like:
        "1.23,4.56,7.89"
        "roll: 1.23, pitch: 4.56, yaw: 7.89"
        "1 2 3"
    """
    try:
        nums = [float(x) for x in re.findall(r"[-+]?\d*\.\d+|[-+]?\d+", line)]
        if len(nums) >= 3:
            roll, pitch, yaw = nums[0], nums[1], nums[2]
            return roll, pitch, yaw
    except Exception:
        pass
    return None, None, None


def human_readable_gps(nmea_line: str) -> str:
    """
    Convert a NMEA line (e.g. $GPGGA...) into a human-readable GPS status string.
    If parsing fails, returns a truncated raw line.
    """
    try:
        msg = pynmea2.parse(nmea_line)
    except Exception:
        # Fallback to raw if we can't parse
        return nmea_line[:80]

    # GGA has position + altitude
    if isinstance(msg, pynmea2.types.talker.GGA):
        lat = msg.latitude
        lon = msg.longitude
        alt = msg.altitude
        units = msg.altitude_units
        sats = msg.num_sats
        quality = msg.gps_qual  # 0 = invalid, 1 = GPS, 2 = DGPS, etc.
        return (
            f"GPS: lat {lat:.5f}, lon {lon:.5f}, alt {alt} {units}, "
            f"sats {sats}, fix {quality}"
        )

    # RMC has lat/lon + ground speed/course/time
    if isinstance(msg, pynmea2.types.talker.RMC):
        lat = msg.latitude
        lon = msg.longitude
        spd = msg.spd_over_grnd  # knots
        cog = msg.true_course
        date = msg.datestamp
        return (
            f"GPS: lat {lat:.5f}, lon {lon:.5f}, "
            f"speed {spd} kn, course {cog}°, date {date}"
        )

    # Fallback for other message types
    return f"GPS: {msg.__class__.__name__} " + nmea_line[:60]


########################
# Main Window          #
########################

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.gs = GroundStation()

        # IMU state (relative to initial reading)
        self.roll_deg = 0.0
        self.pitch_deg = 0.0
        self.yaw_deg = 0.0

        # For "assume it starts flat": baseline calibration on first IMU packet
        self._imu_calibrated = False
        self._roll_zero = 0.0
        self._pitch_zero = 0.0

        # GPS display string
        self.last_gps_string = ""

        self.video_thread = None
        self.imu_thread = None
        self.gps_thread = None

        self.setWindowTitle("Quadcopter Ground Station (Horizon HUD)")

        # --- Widgets ---
        self.video_label = QLabel("Waiting for video...")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(640, 360)

        # --- Layout ---
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.video_label)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Start all threads automatically
        self.start_video()
        self.start_imu()
        self.start_gps()

    # ========== Video ==========
    def start_video(self):
        if self.video_thread is not None and self.video_thread.isRunning():
            return

        self.video_thread = VideoThread(self.gs)
        self.video_thread.frame_received.connect(self.update_video_frame)
        self.video_thread.start()

    def update_video_frame(self, frame: np.ndarray):
        # If your camera is physically upside-down, keep the base 180° flip.
        # Comment this out if you want the raw orientation instead.
        frame = cv2.flip(frame, -1)

        h, w = frame.shape[:2]
        overlay_frame = frame.copy()

        # ----- Draw artificial horizon based on roll/pitch -----
        cx, cy = w / 2.0, h / 2.0

        # Convert to radians
        roll_rad = np.deg2rad(self.roll_deg)
        pitch_rad = np.deg2rad(self.pitch_deg)

        # Vertical shift for pitch (tunable gain)
        pitch_scale = h / 4.0  # bigger => more vertical movement per radian
        center_y = cy + pitch_scale * pitch_rad

        # Line direction for horizon:
        # roll = 0 -> horizontal line
        # roll > 0 -> tilt
        line_len = max(w, h)  # long enough to span across
        dx = (line_len / 2.0) * np.cos(roll_rad)
        dy = (line_len / 2.0) * np.sin(roll_rad)

        pt1 = (int(cx - dx), int(center_y - dy))
        pt2 = (int(cx + dx), int(center_y + dy))

        # Draw horizon line
        cv2.line(
            overlay_frame,
            pt1,
            pt2,
            (0, 255, 0),  # green
            2,
            cv2.LINE_AA,
        )

        # Optional: draw a small center marker
        cv2.circle(
            overlay_frame,
            (int(cx), int(cy)),
            4,
            (0, 255, 0),
            -1,
            cv2.LINE_AA,
        )

        # ----- GPS text at bottom -----
        if self.last_gps_string:
            cv2.putText(
                overlay_frame,
                self.last_gps_string[:110],
                (10, h - 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 255),  # yellow
                2,
                cv2.LINE_AA,
            )

        # Convert BGR (OpenCV) to RGB (Qt)
        rgb_frame = cv2.cvtColor(overlay_frame, cv2.COLOR_BGR2RGB)
        h2, w2, ch = rgb_frame.shape
        bytes_per_line = ch * w2
        qimg = QImage(rgb_frame.data, w2, h2, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)

        self.video_label.setPixmap(
            pixmap.scaled(
                self.video_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )

    # ========== IMU ==========
    def start_imu(self):
        if self.imu_thread is not None and self.imu_thread.isRunning():
            return

        self.imu_thread = IMUThread(self.gs)
        self.imu_thread.line_received.connect(self.update_imu_from_line)
        self.imu_thread.start()

    def update_imu_from_line(self, line: str):
        roll, pitch, yaw = parse_imu_line_to_rpy(line)
        if roll is None and pitch is None and yaw is None:
            return

        # On first valid reading, capture baseline as "flat"
        if not self._imu_calibrated:
            if roll is not None:
                self._roll_zero = roll
            if pitch is not None:
                self._pitch_zero = pitch
            self._imu_calibrated = True
            print(
                f"IMU calibrated: roll_zero={self._roll_zero:.2f}, "
                f"pitch_zero={self._pitch_zero:.2f}"
            )

        # Store relative angles
        if roll is not None:
            self.roll_deg = roll - self._roll_zero
        if pitch is not None:
            self.pitch_deg = pitch - self._pitch_zero
        if yaw is not None:
            self.yaw_deg = yaw  # not used yet, but kept around

    # ========== GPS ==========
    def start_gps(self):
        if self.gps_thread is not None and self.gps_thread.isRunning():
            return

        self.gps_thread = GPSThread(self.gs)
        self.gps_thread.line_received.connect(self.update_gps_display)
        self.gps_thread.start()

    def update_gps_display(self, nmea_line: str):
        # Only parse "main" GPS sentences for overlay
        if nmea_line.startswith(("$GPGGA", "$GNGGA", "$GPRMC", "$GNRMC")):
            self.last_gps_string = human_readable_gps(nmea_line)

    # ========== Cleanup ==========
    def closeEvent(self, event):
        # Stop threads cleanly on window close
        if self.video_thread is not None:
            self.video_thread.stop()
        if self.imu_thread is not None:
            self.imu_thread.stop()
        if self.gps_thread is not None:
            self.gps_thread.stop()
        super().closeEvent(event)


########################
# Entry Point          #
########################

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
