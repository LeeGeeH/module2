# -*- coding: utf-8 -*-
import numpy as np
import logging

logger = logging.getLogger(__name__)

class LocalizationEvaluator:
    def __init__(self, shared, shared_lock):
        self.shared = shared
        self.shared_lock = shared_lock

    def evaluate(self):
        with self.shared_lock:
            player_pos = self.shared.get('playerPos', {'x': 0, 'z': 0, 'y': 0})
            map_points = self.shared.get('map_points', np.array([]))
            if map_points.size > 0:
                distances = np.linalg.norm(map_points[:, :2] - np.array([player_pos['x'], player_pos['z']]), axis=1)
                min_distance = np.min(distances)
                nearest_idx = np.argmin(distances)
                self.shared['error_distance'] = min_distance
                self.shared['nearest_point'] = map_points[nearest_idx, :2]
            else:
                self.shared['error_distance'] = 0.0
                self.shared['nearest_point'] = None