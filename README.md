# Vision_Robot_2026

## About
This project is part of my PhD research. 
Its goal is to enhance the capabilities of an industrial robot by integrating machine vision.

**Project under development!!!**

### Current stage:
v0.6 - Ultrasound Therapy Project (2D)

### Last changes:
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

v0.6.6 - 16.08.2026

* Fixed (again) application crash that occurred when no object was detected.
* Updated algorithm that calculates trajectory reverses after reaching specified distance.
* Changed method of measuring angle of found object.
* Cleaned up the settings.

v0.6.5 - 12.08.2026

* Updated the object detection function result to include a flag indicating whether an object was found.
* Fixed application crash that occurred when no object was detected.
* Added function for calculating a 2D rotation matrix.
* Fixed the detected object angle calculation.
* Improved movement visualization.

