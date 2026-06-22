import numpy as np
import time

class PID3D:
    def __init__(self, Kp, Ki, Kd):
        self.Kp = np.array(Kp, dtype=np.float32)
        self.Ki = np.array(Ki, dtype=np.float32)
        self.Kd = np.array(Kd, dtype=np.float32)

        self.integral = np.zeros(3)
        self.prev_error = np.zeros(3)
        self.prev_time = time.time()

    def update(self, r_robot, r_target):
        s_error = r_target - r_robot

        current_time = time.time()
        dt = current_time - self.prev_time
        if dt <=0:
            dt = 1e-6
        
        # PID components
        P = self.Kp * s_error
        self.integral += s_error * dt
        I = self.Ki * self.integral
        D = self.Kd * (s_error - self.prev_error) / dt

        # save state
        self.prev_error = s_error
        self.prev_time = current_time

        # control output
        return P + I + D
    

# example of use PID controller
# pid = PID3D(Kp=[1.2, 1.2, 1.2],
#             Ki=[0.1, 0.1, 0.1],
#             Kd=[0.05, 0.05, 0.05])

# s_control = pid.update(robot_current_position[:3], r_prediction)
