import socket
import sys

HOST = "0.0.0.0"
PORT = 5002

def main():
	try:
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		# Increase buffer slightly for typical NMEA bursts
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)
		sock.bind((HOST, PORT))
		print(f"Listening for GPS UDP packets on {HOST}:{PORT} (Ctrl+C to stop)")
	except OSError as e:
		print(f"Failed to bind UDP socket on {HOST}:{PORT}: {e}")
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

if __name__ == "__main__":
	main()