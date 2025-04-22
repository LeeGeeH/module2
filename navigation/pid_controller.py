# -*- coding: utf-8 -*-
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PIDController:
    def __init__(self, kp=0.07, ki=0.0, kd=0.0, dt=1.0):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.dt = dt
        self.integral = 0.0
        self.previous_error = 0.0

    def update_gains(self, kp, ki, kd, dt):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.dt = dt

    def compute(self, setpoint, measured_value):
        try:
            error = setpoint - measured_value
            self.integral += error * self.dt
            derivative = (error - self.previous_error) / self.dt if self.dt > 0 else 0.0
            output = self.kp * error + self.ki * self.integral + self.kd * derivative
            self.previous_error = error
            logger.debug(f"PID compute: error={error}, integral={self.integral}, derivative={derivative}, output={output}")
            return output
        except Exception as e:
            logger.error(f"Error in PID compute: {str(e)}")
            return 0.0

class PIDDegController(PIDController):
    def compute(self, setpoint, measured_value):
        try:
            error = setpoint - measured_value
            error = ((error + 180) % 360) - 180
            self.integral += error * self.dt
            derivative = (error - self.previous_error) / self.dt if self.dt > 0 else 0.0
            output = self.kp * error + self.ki * self.integral + self.kd * derivative
            self.previous_error = error
            logger.debug(f"PIDDeg compute: error={error}, integral={self.integral}, derivative={derivative}, output={output}")
            return output
        except Exception as e:
            logger.error(f"Error in PIDDeg compute: {str(e)}")
            return 0.0