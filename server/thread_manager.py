# -*- coding: utf-8 -*-
import threading
import logging
from server.flask_server import run_flask
from server.dash_server import run_dash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ThreadManager:
    def __init__(self, shared_lock):
        self.shared_lock = shared_lock
        self.threads = []

    def start_flask(self):
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        self.threads.append(flask_thread)
        flask_thread.start()
        logger.info("Flask thread started")

    def start_dash(self):
        dash_thread = threading.Thread(target=run_dash, daemon=True)
        self.threads.append(dash_thread)
        dash_thread.start()
        logger.info("Dash thread started")

    def start_servers(self):
        self.start_flask()
        self.start_dash()

    def join(self):
        for thread in self.threads:
            thread.join()