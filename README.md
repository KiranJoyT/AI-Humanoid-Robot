AI Humanoid Robot

An AI-enabled humanoid robot project combining computer vision, voice interaction, servo-based motion control, bipedal locomotion, and sensor feedback.

Project Overview

This project explores the integration of artificial intelligence, embedded systems, electronics, and robotic motion to build an interactive humanoid robot.
The project currently contains three Python programs for intelligent human-robot interaction, standing-pose calibration, and prototype bipedal walking.

Key Features

1. Human-Robot Interaction

* Camera-based person and object detection using OpenCV and YOLOv3-tiny
* Camera pan/tilt tracking using servo motors
* Emotion/state-based OLED facial expressions
* Wake-word detection using Porcupine
* Speech recognition and AI-powered responses using Groq
* Text-to-speech using Piper
* Servo-based greeting gestures

2. Standing Posture Control

* Calibrated servo positions for both legs
* Configurable joint angles
* Basic servo-angle limits

3. Prototype Walking Controller

* Servo-based leg movement sequencing
* MPU6050 accelerometer-based roll feedback for weight shifting
* Ultrasonic distance measurement for obstacle detection
* Standing-pose reset between movement phases

Hardware

* Raspberry Pi 4
* PCA9685 servo controller
* Servo motors
* Raspberry Pi Camera Module
* MPU6050 IMU
* HC-SR04 ultrasonic sensor
* OLED display
* Microphone and speaker

*Hardware listed here should be adjusted to match the final assembled robot.*

Software and Libraries

* Python
* OpenCV
* NumPy
* Picamera2
* Adafruit ServoKit
* SpeechRecognition
* Porcupine and PvRecorder
* Groq API
* Piper TTS
* Raspberry Pi GPIO
* MPU6050 Python library

Project Structure

AI-Humanoid-Robot/
├── README.md
├── .gitignore
└── src/
    ├── humanoid_interaction.py
    ├── standing_pose.py
    └── walking_controller.py


Important Notes

* The three programs are separate prototypes and are not yet presented as one integrated control system.
* Walking and balance behaviour require further testing and calibration on the physical robot.
* Required model files, API credentials, and hardware configuration must be set up separately.
* Test servo movements carefully with the robot supported securely before attempting to walk.

Future Improvements

* Integrate the three programs under a common robot state controller.
* Improve gait sequencing and closed-loop balance control.
* Add robust sensor error handling and obstacle avoidance.
* Explore ROS 2 integration.
* Record demonstrations and document hardware connections.

Author

Kiran Joy T
Robotics & Automation Engineer

GitHub: https://github.com/KiranJoyT
