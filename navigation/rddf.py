# -*- coding: utf-8 -*-
import csv
import os
import logging
import pandas as pd
from utils.config import SHARED
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Rddf:
    def add_info(self, info_data: dict):
        player_pos = info_data.get("playerPos", {})
        x = player_pos.get("x")
        z = player_pos.get("z")
        y = player_pos.get("y", 0)
        speed = info_data.get("playerSpeed")
        return [x, z, y, speed]

    def save(self, data, filename="data/logs/rddf.csv", max_rows=1000):
        try:
            if isinstance(data[0], (int, float)):
                data = [data]
            file_exists = os.path.exists(filename)
            if file_exists:
                df = pd.read_csv(filename)
                df = pd.concat([df, pd.DataFrame(data, columns=["x", "z", "y", "speed"])])
                df = df.tail(max_rows)
                df.to_csv(filename, index=False)
            else:
                with open(filename, "w", newline="") as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(["x", "z", "y", "speed"])
                    writer.writerows(data)

            if 'rddf_data' not in SHARED:
                SHARED['rddf_data'] = []
            SHARED['rddf_data'].extend(data)
            SHARED['rddf_data'] = SHARED['rddf_data'][-max_rows:]

            logger.info(f"Saved CSV file: {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error saving RDDF: {str(e)}")
            raise