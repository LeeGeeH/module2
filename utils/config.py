# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import threading

# 서버 설정
SERVER_CONFIG = {
    "flask_port": 5050,
    "dash_port": 8050,
    "max_obstacles": 50
}

# 그래프 설정
GRAPH_CONFIG = {
    "max_speed": 80,
    "max_points": 100,
    "max_obstacles": 50,
    "max_path_points": 200
}

# PID 설정
PID_CONFIG = {
    "kp": 0.5,
    "ki": 0.1,
    "kd": 0.05
}

PID_CONFIG_DEG = {
    "kp": 0.5,
    "ki": 0.1,
    "kd": 0.05
}

# 공유 데이터
SHARED = {
    "playerPos": {"x": 0, "z": 0, "y": 0},
    "pre_playerPos": {"x": 0, "z": 0, "y": 0},
    "tank_cur_vel_ms": 0.0,
    "tank_tar_vel_kh": 0.0,
    "tank_cur_yaw_deg": 0.0,
    "tank_tar_yaw_deg": 0.0,
    "vel_data": [],
    "del_playerPos": {"x": [], "z": []},
    "destination": None,
    "obstacles": [],
    "path": [],
    "nearest_point": None,
    "error_distance": 0.0,
    "map_points": None,
    "vel_pid": PID_CONFIG.copy(),
    "steer_pid": PID_CONFIG_DEG.copy(),
    "rddf_data": []
}

# 공유 락
shared_lock = threading.Lock()

# 지도 데이터 로드
try:
    df = pd.read_csv("data/map/interpolated_map_with_distance.csv")
    SHARED['map_points'] = df[['x', 'z', 'y']].values
except FileNotFoundError:
    SHARED['map_points'] = np.array([[0, 0, 0], [10, 10, 10], [20, 20, 20], [30, 30, 30]])