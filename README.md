# QuadCopter Embedded Project

# Overview
This project is a quadcopter HUD primarialy for experimentation with different embedded tech stacks.

# Hardware Overview

## Computers and Microcontrollers
- ArduoPilot Mega 2.8 Flight Controller.
- Rasberry Pi 4 running Pi OS.
- Arduino Uno 3 running FreeRTOS.

## Sensors and Modules
- IMU module.
- GPS module.
- Ultrasonic Sensor.
- Camera Module.

## Other Components
- QuadCopter Frame.
- Radio Transmitter and Receiver.
- Electronic Speed Controllers (ESCs) 4x.
- Brushless Motors 4x.
- Propellers 4x.
- LiPo Battery.
- External battery bank (for Rasberry Pi and Arduino).

# How to Run Instructions

## High Frequency Sensor Coordination Unit (Arduino Uno)
1. Connect the arduino to the rasberry pi via USB. We boot right into the program, the RTOS kicks off and takes over from here. 

## Onboard Computer Setup (Raspberry Pi)
1. Install necessary dependencies:
    ```bash
    sudo apt-get update
    sudo apt-get install ffmpeg
    cd ~/QuadCopterEmbeddedProject/onboard-computer
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements-onboard-computer.txt
    ```
2. Connect the camera module, GPS and arduino to the Raspberry Pi.

3. Start the video stream:
    ```bash
    chmod +x start_video_stream
    ./start_video_stream
    ```
4. Start the GPS data sender:
    ```bash
    python3 gps_sender.py
    ```

5. Start the arduino data relayer:
    ```bash
    python sensor_sender.py
    ```

## Ground Station Setup (My laptop running WSL)

1. Install necessary dependencies and create virtual environment:
```bash
   python3 -m venv ground-station-env
   source ground-station-env/bin/activate
   cd ~/QuadCopterEmbeddedProject/ground-station
   pip install -r requirements-ground-station.txt
```

2. 

