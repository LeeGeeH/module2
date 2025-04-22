# -*- coding: utf-8 -*-
import logging
from flask import Flask, request
from navigation.navigation import navigation
from utils.config import SERVER_CONFIG, SHARED, shared_lock

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/info', methods=['POST'])
def update_info():
    data = request.get_json()
    with shared_lock:
        SHARED['playerPos'] = data.get('playerPos', SHARED['playerPos'])
        SHARED['tank_cur_vel_ms'] = data.get('playerSpeed', 0.0)
        SHARED['tank_cur_yaw_deg'] = data.get('playerBodyX', 0.0)
        SHARED['pre_playerPos'] = SHARED['playerPos'].copy()
        navigation.rddf.save(navigation.rddf.add_info(data))
    return {"status": "success"}

@app.route('/get_move', methods=['GET'])
def get_move():
    result = navigation.get_move()
    logger.info(f"Get Move - Command: {result['command']}, Speed: {result['speed'] * 3.6} km/h, Yaw: {result['yaw']} deg")
    return result

def run_flask():
    app.run(port=SERVER_CONFIG['flask_port'], debug=False, use_reloader=False)