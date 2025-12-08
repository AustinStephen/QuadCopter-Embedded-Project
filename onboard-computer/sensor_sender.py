"""
Read serial data from the Arduino sensors and send over UDP to the ground station.
"""
import serial
import socket

ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)

DEST_IP = '192.168.0.9'   
DEST_PORT = 5002          
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try:
    while True:
        raw = ser.readline().decode('utf-8', errors='ignore').strip()
        if raw:
            try:
                sock.sendto((raw + '\n').encode('utf-8'), (DEST_IP, DEST_PORT))
            except Exception as e:
                print(f"UDP send error: {e}")
                
except KeyboardInterrupt:
    print("Stopping GPS reader")
finally:
    ser.close()
    sock.close()
