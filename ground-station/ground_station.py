"""Ground Station Class.
-> cv2 is making my linter mad here for some reason.
"""
import sys
# pylint: disable=no-member
import cv2
import socket
import time

class GroundStation:
    """A class to represent a Ground Station for a quadcopter project."""
    def __init__(self, ipAddress = "0.0.0.0", videoStreamURL = "udp://0.0.0.0:5000", gpsPort = 5001, imuPort = 5002):
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
        
        # Try to open the IMU socket and leave it open for future use
        try:
            self.imuSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Increase buffer slightly for typical NMEA bursts
            self.imuSocket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)
            self.imuSocket.bind((self.ipAddress,imuPort))
            print(f"Listening for IMU UDP packets on {self.ipAddress}:{imuPort} (Ctrl+C to stop)")
        except OSError as e:
            print(f"Failed to bind UDP socket on {self.ipAddress}:{imuPort}: {e}")
            sys.exit(1)
            
        # Try to open the GPS socket  and leave it open for future use
        try:
            self.gpsSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Increase buffer slightly for typical NMEA bursts
            self.gpsSocket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)
            self.gpsSocket.bind((self.ipAddress, gpsPort))
            print(f"Listening for GPS UDP packets on {self.ipAddress}:{gpsPort} (Ctrl+C to stop)")
        except OSError as e:
            print(f"Failed to bind UDP socket on {self.ipAddress}:{gpsPort}: {e}")
            sys.exit(1)
            
    def __del__(self):
        """Destructor to close sockets to the quadcopter onboard brain."""
        self.imuSocket.close()
        self.gpsSocket.close() 
        
    def updateIMU(self):
        """Update the IMU data from the quadcopter.
        """
        data, addr = self.imuSocket.recvfrom(4096)
        # Assume UTF-8 or ASCII; replace errors to avoid crashes on bad bytes
        text = data.decode("utf-8", errors="replace")
        # Many GPS feeds send NMEA lines terminated by \r\n; print as-is
        print(f"Saving IMU [{addr[0]}:{addr[1]}] {text.strip()}")
        self.roll, self.pitch, self.yaw = map(float, text.strip().split(','))
        

    ##### Stream functions (Only useful for debugging) ###### 
    # Opens and prints a continuous stream of the data from the onboard computer.
    
    def viewIMUStream(self, timeout=30):
        """ 
        Open continuous IMU data stream 
        """
        print("Starting IMU Stream for", timeout, "seconds...")
        start_time = time.now()
        while (time.now() - start_time).seconds < timeout:
            data, addr =  self.imuSocket.recvfrom(4096)
            # Assume UTF-8 or ASCII; replace errors to avoid crashes on bad bytes
            text = data.decode("utf-8", errors="replace")
            # Many GPS feeds send NMEA lines terminated by \r\n; print as-is
            print(f"[{addr[0]}:{addr[1]}] {text.strip()}")
  
  
    def viewGPSStream(self, timeout=30):
        """Open a continuous gps stream from the on board computer.
        """
        print("Starting GPS Stream for", timeout, "seconds...")
        start_time = time.now()
        while (time.now() - start_time).seconds < timeout:
            data, addr = self.gpsSocket.recvfrom(4096)
            # Assume UTF-8 or ASCII; replace errors to avoid crashes on bad bytes
            text = data.decode("utf-8", errors="replace")
            # Many GPS feeds send NMEA lines terminated by \r\n; print as-is
            print(f"[{addr[0]}:{addr[1]}] {text.strip()}")


    def viewVideoStream(self, timeout=30):
        """Creates the video stream 
        """
        print("Starting Video Stream for", timeout, "seconds...")
         # Open a UDP video stream using OpenCV
        cap = cv2.VideoCapture(self.videoStreamURL, cv2.CAP_FFMPEG)
        if not cap.isOpened():
            print("Could not open UDP stream")
            exit(1)
        start_time = time.now()
        while (time.now() - start_time).seconds < timeout:
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