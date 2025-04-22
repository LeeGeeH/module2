# -*- coding: utf-8 -*-
import threading
import logging
import numpy as np
from navigation.rddf import Rddf
from navigation.speed_plan import SpeedPlan
from navigation.steering_plan import SteeringPlan
from navigation.position_handler import PositionHandler
from navigation.localization_evaluator import LocalizationEvaluator
from utils.config import SHARED, shared_lock

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PathPlanning:
    def calculate_path(self):
        with shared_lock:
            current_pos = SHARED.get('playerPos', {'x': 0, 'z': 0, 'y': 0})
            start = (current_pos['x'], current_pos['z'])
            destination = SHARED.get('destination', None)

            if not destination:
                logger.warning("No destination set, using temporary destination (100, 100, 0)")
                SHARED['destination'] = (100, 100, 0)
                destination = SHARED['destination']

            dest_x, dest_y, dest_z = destination
            end = (dest_x, dest_z)
            SHARED['path'] = [start, end]
            logger.info(f"Calculated path: {SHARED['path']}")

class Navigation:
    def __init__(self):
        self.path_planning = PathPlanning()
        self.rddf = Rddf()
        self.speed_plan = SpeedPlan(SHARED, shared_lock)
        self.steering_plan = SteeringPlan(SHARED, shared_lock)
        self.position_handler = PositionHandler(SHARED, shared_lock)
        self.localization_evaluator = LocalizationEvaluator(SHARED, shared_lock)
        self.running = False

    def start(self):
        self.running = True
        threading.Thread(target=self.run, daemon=True).start()

    def run(self):
        while self.running:
            with shared_lock:
                self.path_planning.calculate_path()
                self.localization_evaluator.evaluate()
            threading.Event().wait(0.1)

    def get_move(self, dt=0.1):
        with shared_lock:
            # 위치 및 오차 업데이트
            self.position_handler.update_position()
            self.localization_evaluator.evaluate()

            # 속도와 조향 계산
            speed = self.speed_plan.plan(dt)
            yaw = self.steering_plan.plan(dt)

            # 목적지 도달 여부 확인
            destination = SHARED.get('destination', None)
            error_distance = SHARED.get('error_distance', float('inf'))
            logger.info(f"Navigation - Error Distance: {error_distance}, Destination: {destination}, Player Pos: {SHARED['playerPos']}")
            if destination and error_distance < 0.5:
                SHARED['tank_tar_vel_kh'] = 0
                SHARED['tank_cur_vel_ms'] = 0
                SHARED['tank_tar_yaw_deg'] = 0
                SHARED['tank_cur_yaw_deg'] = 0
                self.speed_plan.reset()
                self.steering_plan.reset()
                logger.info("Destination reached, stopping and resetting PID controllers.")
                return {"command": "STOP", "speed": 0, "yaw": 0}

            # 속도에 따라 명령 생성
            if abs(SHARED['tank_cur_vel_ms']) < 0.1:
                command = "STOP"
            else:
                command = "W"

            logger.info(f"Navigation - Get Move - Command: {command}, Speed: {SHARED['tank_cur_vel_ms'] * 3.6} km/h, Yaw: {SHARED['tank_cur_yaw_deg']} deg")
            return {
                "command": command,
                "speed": SHARED['tank_cur_vel_ms'],
                "yaw": SHARED['tank_cur_yaw_deg']
            }

    def shutdown(self):
        self.running = False

navigation = Navigation()