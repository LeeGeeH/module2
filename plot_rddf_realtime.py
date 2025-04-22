import threading
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import pandas as pd
import logging
from utils.config import SHARED

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RddfRealtimePlotter:
    def __init__(self, shared_lock, interval=500):
        self.shared_lock = shared_lock
        self.interval = interval
        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        self.line, = self.ax.plot([], [], 'b.-', label='RDDF Trajectory')
        self.current_pos, = self.ax.plot([], [], 'ro', label='Current Position', markersize=10)
        self.setup_plot()

    def setup_plot(self):
        self.ax.set_xlabel('X Position')
        self.ax.set_ylabel('Z Position')
        self.ax.set_title('Real-Time RDDF Trajectory (X vs Z)')
        self.ax.set_xlim(0, 300)
        self.ax.set_ylim(0, 300)
        self.ax.grid(True)
        self.ax.legend()

    def update(self, frame):
        with self.shared_lock:
            rddf_data = SHARED.get('rddf_data', [])
            if 'pre_playerPos' not in SHARED or not all(key in SHARED['pre_playerPos'] for key in ['x', 'z']):
                logger.warning("pre_playerPos not properly initialized, using default values")
                current_pos = (0, 0)
            else:
                current_pos = (SHARED['pre_playerPos']['x'], SHARED['pre_playerPos']['z'])

        if rddf_data:
            df_rddf = pd.DataFrame(rddf_data, columns=['x', 'z', 'y', 'speed'])
            rddf_x = df_rddf['x'].values
            rddf_z = df_rddf['z'].values
            self.line.set_data(rddf_x, rddf_z)
        else:
            self.line.set_data([], [])

        self.current_pos.set_data([current_pos[0]], [current_pos[1]])
        return self.line, self.current_pos

    def run(self):
        ani = FuncAnimation(self.fig, self.update, interval=self.interval, blit=True)
        plt.show()

def run_rddf_realtime_plot(shared_lock):
    try:
        plotter = RddfRealtimePlotter(shared_lock)
        # Matplotlib의 GUI는 메인 스레드에서 실행되도록 함
        plt.show()
    except Exception as e:
        logger.error(f"Error in RDDF real-time plotter: {str(e)}")

# Run plotter in main thread
if __name__ == "__main__":
    # 여기서 main thread에서 실행하도록 보장합니다.
    shared_lock = threading.Lock()
    run_rddf_realtime_plot(shared_lock)
