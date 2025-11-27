import cv2

# Listen for the UDP stream sent to this machine on port 5000
# Try one of these:
#   "udp://0.0.0.0:5000"  (bind on all interfaces)
#   "udp://@:5000"        (ffmpeg-style syntax, often also works)
STREAM_URL = "udp://0.0.0.0:5000"

cap = cv2.VideoCapture(STREAM_URL, cv2.CAP_FFMPEG)

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
