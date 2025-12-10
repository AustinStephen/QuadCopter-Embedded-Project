from ground_station import GroundStation

def main():
    """Entry function"""
    # Note I'm relying on a lot of the default parameters here.
    gs = GroundStation()
    # Loop the streams to demo functionality
    for _ in range(3):
        gs.viewVideoStream(5)
        gs.viewGPSStream(5)
        gs.viewIMUStream(5)
    # Cleanup
    del gs

if __name__ == "__main__":
    main()
    
