# Vision_Robot_2026

## About
This project is part of my PhD research. 
Its goal is to enhance the capabilities of an industrial robot by integrating machine vision.

**Project under development!!!**

### Current stage:
v0.6 - Following trajectory on moving surface

### Last changes:
v0.6.2 - 30.07.2026

* Added preview of the robot's workspace.
* Added functions to generate the robot's trajectory:
    * on a straight line,
    * ​​on a sinusoidal path.

v0.6.1 - 28.07.2026

* Changed the robot's HOME position.
* Prepared functions for detecting the hand position.
* Prepared new main program (main_ultrasound_therapy_2D) for future hand therapy.
* Added debugging tools that will be used in future tests.

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

