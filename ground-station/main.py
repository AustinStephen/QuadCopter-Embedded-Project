from ground_station import GroundStation

def main():
    """Entry function"""
    # Note I'm relying on a lot of the default parameters here.
    gs = GroundStation()
    # Loop the streams to demo functionality
    for _ in range(10):
        gs.viewVideoStream(10)
        gs.viewGPSStream(10)
        gs.viewIMUStream(10)
    # Cleanup
    gs.__del__()

if __name__ == "__main__":
    main()
    
