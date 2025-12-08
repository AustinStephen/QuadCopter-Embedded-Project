"""Ground Station Class
"""
import sys
import cv2
import socket

class GroundStation:
    """A class to represent a Ground Station for a quadcopter project."""
    def __init__(self, ipAddress = "0.0.0.0", videoStreamURL = "udp://0.0.0.0:5000", gpsSocket = 5001, imuSocket = 5002):
        """
        Initializes the GroundStation and ensure the sockets/URL match on the onboard system."""
        self.ipAddress = ipAddress
        self.videoStreamURL = videoStreamURL
        self.roll = 0 
        self.pitch = 0
        self.yaw = 0
        self.latitude = 0
        self.longitude = 0
        self.altitude = 0
        self.groundProximity = 0
        self.gpsSocket = gpsSocket
        self.imuSocket = imuSocket
    
        
    def openIMUStream(self):
        """ 
        Open continuous IMU data stream 
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Increase buffer slightly for typical NMEA bursts
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)
            sock.bind((self.ipAddress, self.imuSocket))
            print(f"Listening for GPS UDP packets on {self.ipAddress}:{self.imuSocket} (Ctrl+C to stop)")
        except OSError as e:
            print(f"Failed to bind UDP socket on {self.ipAddress}:{self.imuSocket}: {e}")
            sys.exit(1)

        try:
            while True:
                data, addr = sock.recvfrom(4096)
                # Assume UTF-8 or ASCII; replace errors to avoid crashes on bad bytes
                text = data.decode("utf-8", errors="replace")
                # Many GPS feeds send NMEA lines terminated by \r\n; print as-is
                print(f"[{addr[0]}:{addr[1]}] {text.strip()}")
        except KeyboardInterrupt:
            print("\nStopping GPS receiver...")
        finally:
            sock.close()
  
  
    def opengetGPSStream(self):
        """Open a continuous gps stream from the on board computer.
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Increase buffer slightly for typical NMEA bursts
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)
            sock.bind((self.ipAddress, self.gpsSocket))
            print(f"Listening for GPS UDP packets on {self.ipAddress}:{self.gpsSocket} (Ctrl+C to stop)")
        except OSError as e:
            print(f"Failed to bind UDP socket on {self.ipAddress}:{self.gpsSocket}: {e}")
            sys.exit(1)

        try:
            while True:
                data, addr = sock.recvfrom(4096)
                # Assume UTF-8 or ASCII; replace errors to avoid crashes on bad bytes
                text = data.decode("utf-8", errors="replace")
                # Many GPS feeds send NMEA lines terminated by \r\n; print as-is
                print(f"[{addr[0]}:{addr[1]}] {text.strip()}")
        except KeyboardInterrupt:
            print("\nStopping GPS receiver...")
        finally:
            sock.close()


    def openVideoStream(self):
        cap = cv2.VideoCapture(self.videoStreamURL, cv2.CAP_FFMPEG)

        if not cap.isOpened():
            print("Could not open UDP stream")
            exit(1)

        while True:
            ret, frame = cap.read()
            if not ret:
                print("No frame received (stream might not be coming in)")
                break

            cv2.imshow("UDP Camera Stream", frame)

            # Press 'q' to quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()