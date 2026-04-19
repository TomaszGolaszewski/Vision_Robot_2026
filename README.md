# Vision_Robot_2026

## About
This project is part of my PhD research. 
Its goal is to enhance the capabilities of an industrial robot by integrating machine vision.

**Project under development!!!**

### Current stage:
v0.4 - Multithreading with TCP client

### Last changes:
v0.4.6 - 19.04.2026

* Added new error reference table;
* Cleaned up the code.

v0.4.5 - 19.04.2026

* Added new functions to retrieve and parse data:
    * request_status() - reqests data from robot;
    * get_and_handle_message_for_robot_motion():
        * function retrieves the robot's current position...
        * ... and data from the robot's position register.

v0.4.4 - 11.04.2026

* Added debugging tool (for sequence 87).

v0.4.3 - 26.03.2026

* Updated robot control system after testing with real robot:
    * switched the main program to TCP client communication interface;
    * completed testing of robot control via the TCP client interface;
    * moved vision and robot settings to common file;
    * cleaned up and standardized terminal message output.

v0.4.2 - 25.03.2026

* Prepared resources for further tests with the robot:
    * added test program for robot control via the TCP client interface;
    * updated movement commands to work in both interfaces.
