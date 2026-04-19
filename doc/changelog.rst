Changelog
======

v0.4.5 - 19.04.2026
------
* Added new functions to retrieve and parse data:
    * request_status() - reqests data from robot;
    * get_and_handle_message_for_robot_motion():
        * function retrieves the robot's current position...
        * ... and data from the robot's position register.

v0.4.4 - 11.04.2026
------
* Added debugging tool (for sequence 87).

v0.4.3 - 26.03.2026
------
* Updated robot control system after testing with real robot:
    * switched the main program to TCP client communication interface;
    * completed testing of robot control via the TCP client interface;
    * moved vision and robot settings to common file;
    * cleaned up and standardized terminal message output.

v0.4.2 - 25.03.2026
------
* Prepared resources for further tests with the robot:
    * added test program for robot control via the TCP client interface;
    * updated movement commands to work in both interfaces.

v0.4.1 - 25.03.2026
------
* Updated TCP client after testing with real robot.
    * TCP client fixes;
    * updated command parsing functions to work in both interfaces.

v0.4.0 - 15.03.2026
------
* Added first version on TCP client;
* Implemented TCP client for further tests with the robot;
* Settings moved to one file.

v0.4 - Multithreading with TCP client
======


v0.3.1 - 15.03.2026
------
* Updated robot motion interface after testing on real robot.

v0.3.0 - 13.03.2026 
------
* Added FakeSocket class to simulate TCP socket for debugging without a real robot.
* Implemented multithreading for further tests with the robot.

v0.3 - Multithreading
======


v0.2.7 - 06.03.2026 
------
* Updated main program after testing on real robot.

v0.2.6 - 05.03.2026 
------
* Updated robot_motion_interface nad main program after testing on real robot.

v0.2.5 - 04.03.2026 
------
* Prepared resources for further tests with the robot
    * added robot response parsing,
    * coupled QR code position detection with robot movement.

v0.2.4 - 04.03.2026
------
* Updated robot motion interface after testing on real robot.

v0.2.3 - 02.03.2026 
------
* Prepared resources for further tests with the robot.

v0.2.2 - 27.02.2026 
------
* Prepared resources for further tests with the robot.

v0.2.1 - 27.02.2026 
------
* Added stabilization of found coordinates;
* Added minor improvements to the stabilization algorithm.

v0.2.0 - 26.02.2026 
------
* Prepared skeleton of the main program.

v0.2 - Proof of concept with 3 DOF (x, y, z)
======


v0.1.9 - 26.02.2026 
------
* Updated robot motion interface after testing on real robot.

v0.1.8 - 22.02.2026 
------
* Added QR code position (x, y, z) calculation relative to the camera.

v0.1.7 - 18.02.2026 
------
* Prepared resources for further tests with the robot.

v0.1.6 - 17.02.2026 
------
* Updated robot motion interface after testing on real robot.

v0.1.5 - 16.02.2026 
------
* Added tests for robot motion.

v0.1.4 - 16.02.2026 
------
* Added QR code detection and decoding.

v0.1.3 - 15.02.2026 
------
* Added tests for vision QR.

v0.1.2 - 15.02.2026 
------
* Added tests for vision 2D;
* Code cleaning.

v0.1.1 - 25.12.2025 
------
* Cloned more assets from project Vision_Blob_2025.

v0.1.0 - 25.12.2025
------
* Project initialization;
* Cloned assets from project Vision_Blob_2025.

v0.1 - Project initialization
======