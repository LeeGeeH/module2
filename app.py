# -*- coding: utf-8 -*-
import logging
from server.thread_manager import ThreadManager
from navigation.navigation import navigation
from utils.config import shared_lock

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting application")
    # SHARED 초기화 (필요 시 추가)
    logger.info("SHARED data has been reset")
    
    thread_manager = ThreadManager(shared_lock)
    navigation.start()
    thread_manager.start_flask()
    thread_manager.start_dash()
    thread_manager.join()

if __name__ == "__main__":
    main()