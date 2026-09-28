# Vision_Robot_2026

## About
This project is part of my PhD research. 
Its goal is to enhance the capabilities of an industrial robot by integrating machine vision.

**Project under development!!!**

### Current stage:
v0.6 - Ultrasound Therapy Project (2D)

### Last changes:
v0.6.11 - 28.09.2026

* Added tool number override (UToolNumber, UFrameNumber).
* Added support for retrieving robot joint positions.
* Added a robot return mechanism.
* Updated the robot's start position to operate in a different configuration.

v0.6.10 - 23.09.2026

* Added robot configuration copying to fix the reorientation issue.

v0.6.9 - 19.08.2026

* Changed the method of calculating the trajectory - now the robot follows the target.

v0.6.8 - 17.08.2026

* Added functionality to maintain the robot's position within specified safe area;
* Added function to simulate robot position change;
* Enabled communication with the robot;
* Changed Kalman filter coefficients.

v0.6.7 - 16.08.2026

* Updated algorithm that calculates sinusoidal trajectory reverses after reaching specified distance;
* Added operating mode switch - linear / sinusoidal;
* Added parameterization of motion along the arm;
* Moved starting point of trajectory to shoulder position.
