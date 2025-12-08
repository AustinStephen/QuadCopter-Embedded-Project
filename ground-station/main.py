from ground_station import GroundStation

def main():
    # Note I'm relying on a lot of the default parameters here.
    gs = GroundStation()
    # s.openVideoStream()
    # gs.opengetGPSStream()
    gs.openIMUStream()

if __name__ == "__main__":
	main()
