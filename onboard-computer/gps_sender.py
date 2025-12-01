import pynmea2
import serial
import socket

ser = serial.Serial('/dev/ttyACM1', 9600, timeout=1)

DEST_IP = '192.168.0.9'   # your desktop's IP
DEST_PORT = 5001          # must match the desktop listener

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

try:
    while True:
        raw = ser.readline().decode('utf-8', errors='ignore').strip()
        if raw:
            # Send every NMEA sentence over UDP
            try:
                sock.sendto((raw + '\n').encode('utf-8'), (DEST_IP, DEST_PORT))
            except Exception as e:
                print(f"UDP send error: {e}")

            if raw.startswith('$GPGGA'):
                try:
                    msg = pynmea2.parse(raw)
                    print(f"GGA: Lat {msg.latitude}°, Lon {msg.longitude}°, Alt {msg.altitude}m, Time {msg.timestamp}")
                except pynmea2.ParseError:
                    print(f"Failed to parse GGA: {raw}")
            elif raw.startswith('$GPVTG'):
                try:
                    msg = pynmea2.parse(raw)
                    print(f"VTG: Course {msg.true_track}°, Speed {msg.spd_over_grnd_kmph} km/h")
                except pynmea2.ParseError:
                    print(f"Failed to parse VTG: {raw}")
            elif raw.startswith('$GPGLL'):
                try:
                    msg = pynmea2.parse(raw)
                    print(f"GLL: Lat {msg.latitude}°, Lon {msg.longitude}°, Time {msg.timestamp}, Status {msg.status}")
                except pynmea2.ParseError:
                    print(f"Failed to parse GLL: {raw}")
except KeyboardInterrupt:
    print("Stopping GPS reader")
finally:
    ser.close()
    sock.close()
