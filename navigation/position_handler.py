# -*- coding: utf-8 -*-
import logging

logger = logging.getLogger(__name__)

class PositionHandler:
    def __init__(self, shared, shared_lock):
        self.shared = shared
        self.shared_lock = shared_lock

    def update_position(self):
        with self.shared_lock:
            self.shared['playerPos'] = self.shared['pre_playerPos']

    def get_position(self):
        with self.shared_lock:
            pos = self.shared.get('playerPos', {'x': 0, 'z': 0, 'y': 0})
            return (pos['x'], pos['z'], pos['y'])

    def get_speed(self):
        with self.shared_lock:
            return self.shared.get('tank_cur_vel_ms', 0.0)