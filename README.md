# Vision_Robot_2026

## About
This project is part of my PhD research. 
Its goal is to enhance the capabilities of an industrial robot by integrating machine vision.

**Project under development!!!**

### Current stage:
v0.6 - Following trajectory on moving surface

### Last changes:
v0.6.0 - 24.06.2026

* Added test script that detects position of bright object (arm) and calculates its orientation.

v0.5.11 - 22.06.2026

* Added a script that moves the robot in one axis (1D) for further diagnostics.
* Added pid controller for further testing.
* Presentation materials added.

v0.5.10 - 27.05.2026

* Refactored vector calculations after tests with the robot.
* Fixed calculations for locating an object regarding right-handed coordinate system.
* Changed data type stored in matrices - from float to np.float32.

v0.5.9 - 24.05.2026

* Added auxiliary elements that will be used in future tests:
    * added functions for calculating rotation matrices;
    * refactored vector calculations (first attempt);
    * added the robot's last position to the 3D graph;
    * added the coordinate recording of the robot's last requested position.

