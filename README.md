# Vision_Robot_2026

## About
This project is part of my PhD research. 
Its goal is to enhance the capabilities of an industrial robot by integrating machine vision.

**Project under development!!!**

### Current stage:
v0.4 - Multithreading with TCP client

### Last changes:
v0.4.8 - 28.04.2026

* Tested version with moving average of relative QR code position (milestones).
* Added version with moving average of global QR code position (also moved to milestones).

v0.4.7 - 26.04.2026

* Prepared resources for further tests with the robot:
    * updated main program with improvements made in previous tests;
    * changed method of setting movement to global coordinates instead of relative ones.

v0.4.6 - 19.04.2026

* Added new error reference table;
* Cleaned up the code.

v0.4.5 - 19.04.2026

* Added new functions to retrieve and parse data:
    * request_status() - reqests data from robot;
    * get_and_handle_message_for_robot_motion():
        * function retrieves the robot's current position...
        * ... and data from the robot's position register.

