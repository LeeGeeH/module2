# -*- coding: utf-8 -*-
import logging
from navigation.pid_controller import PIDDegController

logger = logging.getLogger(__name__)

class SteeringPlan:
    def __init__(self, shared, shared_lock):
        self.shared = shared
        self.shared_lock = shared_lock
        self.pid = PIDDegController(
            kp=self.shared['steer_pid']['kp'],
            ki=self.shared['steer_pid']['ki'],
            kd=self.shared['steer_pid']['kd'],
            dt=0.1
        )

    def plan(self, dt=0.1):
        with self.shared_lock:
            # PID 파라미터 업데이트
            self.pid.update_gains(
                kp=self.shared['steer_pid']['kp'],
                ki=self.shared['steer_pid']['ki'],
                kd=self.shared['steer_pid']['kd'],
                dt=dt
            )

            current_angle = self.shared.get('tank_cur_yaw_deg', 0)
            target_angle = self.shared.get('tank_tar_yaw_deg', 0)
            output = self.pid.compute(target_angle, current_angle)

            # 조향 업데이트
            new_angle = current_angle + output
            if new_angle > 180:
                new_angle -= 360
            elif new_angle < -180:
                new_angle += 360
            self.shared['tank_cur_yaw_deg'] = new_angle

            logger.info(f"SteeringPlan - Target: {target_angle} deg, Current: {new_angle} deg, Output: {output}")
            return new_angle

    def reset(self):
        self.pid.integral = 0.0
        self.pid.previous_error = 0.0