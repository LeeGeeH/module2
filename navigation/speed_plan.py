# -*- coding: utf-8 -*-
import logging
from navigation.pid_controller import PIDController

logger = logging.getLogger(__name__)

class SpeedPlan:
    def __init__(self, shared, shared_lock):
        self.shared = shared
        self.shared_lock = shared_lock
        self.pid = PIDController(
            kp=self.shared['vel_pid']['kp'],
            ki=self.shared['vel_pid']['ki'],
            kd=self.shared['vel_pid']['kd'],
            dt=0.1
        )

    def plan(self, dt=0.1):
        with self.shared_lock:
            # PID 파라미터 업데이트
            self.pid.update_gains(
                kp=self.shared['vel_pid']['kp'],
                ki=self.shared['vel_pid']['ki'],
                kd=self.shared['vel_pid']['kd'],
                dt=dt
            )

            current_speed = self.shared.get('tank_cur_vel_ms', 0.0) * 3.6  # km/h
            target_speed = self.shared.get('tank_tar_vel_kh', 0.0)
            output = self.pid.compute(target_speed, current_speed)

            # 속도 업데이트 (m/s 단위로 변환)
            current_speed_ms = self.shared.get('tank_cur_vel_ms', 0.0)
            new_speed_ms = current_speed_ms + (output / 3.6)  # km/h 단위 출력을 m/s로 변환
            new_speed_ms = max(-60 / 3.6, min(new_speed_ms, 60 / 3.6))  # 최대 속도 제한
            self.shared['tank_cur_vel_ms'] = new_speed_ms

            logger.info(f"SpeedPlan - Target: {target_speed} km/h, Current: {new_speed_ms * 3.6} km/h, Output: {output}")
            return new_speed_ms

    def reset(self):
        self.pid.integral = 0.0
        self.pid.previous_error = 0.0