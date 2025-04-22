# -*- coding: utf-8 -*-
from dash import Dash, dcc, html
from dash.dependencies import Output, Input, State
import plotly.graph_objs as go
from utils.config import SHARED, SERVER_CONFIG, GRAPH_CONFIG, PID_CONFIG, PID_CONFIG_DEG
import pandas as pd
import numpy as np
import threading
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_dash_app():
    app = Dash(__name__)
    shared = SHARED
    shared_lock = threading.Lock()

    app.layout = html.Div([
        html.H4("실시간 속도 시각화"),
        dcc.Graph(id='live-graph'),
        dcc.Interval(id='interval', interval=500, n_intervals=0),

        html.Div([
            html.Label("타겟 속도 (-30~70 km/h)"),
            dcc.Slider(
                id='target-speed-slider',
                min=-30,
                max=70,
                step=1,
                value=0,
                marks={i: f"{i} km/h" for i in range(-30, 71, 10)}
            )
        ], style={'margin-top': '20px'}),

        html.Div(id='target-speed-display', style={'margin-top': '10px', 'font-weight': 'bold'}),

        html.H4("속도 PID 파라미터 조정 (Kp, Ki, Kd)"),
        html.Div([
            html.Label("Kp:"),
            dcc.Input(id='input-kp', type='number', value=shared['vel_pid']['kp'], step=0.0001),
            html.Label("Ki:"),
            dcc.Input(id='input-ki', type='number', value=shared['vel_pid']['ki'], step=0.0001),
            html.Label("Kd:"),
            dcc.Input(id='input-kd', type='number', value=shared['vel_pid']['kd'], step=0.0001),
        ], style={'margin-top': '10px', 'margin-bottom': '10px'}),

        html.Div(id='pid-display', style={'font-weight': 'bold'}),

        html.H4("전차 위치 변화량 (ΔX, ΔZ)", style={'margin-top': '40px'}),
        dcc.Graph(id='delta-pos-graph'),

        html.H4("현재 각도 (deg)", style={'margin-top': '40px'}),
        dcc.Graph(id='steer-gauge'),

        html.H4("타겟 각도 조절 (deg)"),
        dcc.Slider(
            id='target-angle-slider',
            min=-180,
            max=180,
            step=1,
            value=0,
            marks={
                -180: '-180°',
                -90: '-90°',
                0: '0°',
                90: '90°',
                180: '180°'
            }
        ),
        html.Div(id='target-angle-display', style={'margin-top': '10px', 'font-weight': 'bold'}),

        html.H4("조향 PID 파라미터 조정 (Kp, Ki, Kd)", style={'margin-top': '30px'}),
        html.Div([
            html.Label("Kp:"),
            dcc.Input(id='steer-kp', type='number', value=shared['steer_pid']['kp'], step=0.0001),
            html.Label("Ki:"),
            dcc.Input(id='steer-ki', type='number', value=shared['steer_pid']['ki'], step=0.0001),
            html.Label("Kd:"),
            dcc.Input(id='steer-kd', type='number', value=shared['steer_pid']['kd'], step=0.0001),
        ], style={'margin-top': '10px', 'margin-bottom': '10px'}),
        html.Div(id='steer-pid-display', style={'font-weight': 'bold'}),

        html.H4("경로 및 장애물 시각화 (RDDF 궤적 포함)", style={'margin-top': '40px'}),
        dcc.Graph(id='path-obstacle-graph'),

        html.H4("위치 오차 시각화", style={'margin-top': '40px'}),
        dcc.Graph(id='error-distance-graph'),

        html.H4("RDDF 속도 변화", style={'margin-top': '40px'}),
        dcc.Graph(id='rddf-speed-graph'),
    ])

    @app.callback(
        Output('live-graph', 'figure'),
        Input('interval', 'n_intervals')
    )
    def update_graph(n):
        with shared_lock:
            data = shared['vel_data'][-GRAPH_CONFIG['max_points']:]
            current_speed = shared.get('tank_cur_vel_ms', 0.0) * 3.6
            target_speed = shared.get('tank_tar_vel_kh', 0.0)
            logger.info(f"Live Graph - Current Speed: {current_speed} km/h, Target Speed: {target_speed} km/h")
        return {
            'data': [
                go.Scatter(y=data, mode='lines+markers', name='Current Speed'),
                go.Scatter(y=[target_speed] * len(data), mode='lines', name='Target Speed', line=dict(dash='dash'))
            ],
            'layout': go.Layout(
                xaxis=dict(
                    range=[max(0, len(data) - GRAPH_CONFIG['max_points']), len(data)],
                    dtick=10,
                    title='시간 (포인트)'
                ),
                yaxis=dict(
                    range=[-40, GRAPH_CONFIG['max_speed']],
                    dtick=10,
                    title='속도 (km/h)'
                ),
                title='실시간 속도 시각화'
            )
        }

    @app.callback(
        Output('delta-pos-graph', 'figure'),
        Input('interval', 'n_intervals')
    )
    def update_delta_graph(n):
        with shared_lock:
            del_x_data = shared.get('del_playerPos', {}).get('x', [])[-GRAPH_CONFIG['max_points']:]
            del_z_data = shared.get('del_playerPos', {}).get('z', [])[-GRAPH_CONFIG['max_points']:]
        return {
            'data': [
                go.Scatter(y=del_x_data, mode='lines', name='ΔX', line=dict(dash='dot')),
                go.Scatter(y=del_z_data, mode='lines', name='ΔZ', line=dict(dash='dash'))
            ],
            'layout': go.Layout(
                xaxis=dict(
                    title='시간 (포인트)',
                    dtick=10,
                    range=[max(0, len(del_x_data) - GRAPH_CONFIG['max_points']), len(del_x_data)]
                ),
                yaxis=dict(title='좌표 변화량', dtick=1),
                title='전차 위치 변화량 (ΔX, ΔZ)',
                legend=dict(orientation='h')
            )
        }

    @app.callback(
        Output('steer-gauge', 'figure'),
        Input('interval', 'n_intervals')
    )
    def update_steer_gauge(n):
        with shared_lock:
            angle = shared.get('tank_cur_yaw_deg', 0)
            target_angle = shared.get('tank_tar_yaw_deg', 0)
            logger.info(f"Steer Gauge - Current Angle: {angle} deg, Target Angle: {target_angle} deg")
        r_values_blue = np.linspace(0, 0.98, 49)
        theta_values_blue = [angle] * len(r_values_blue)
        blue_dots = go.Scatterpolar(
            r=r_values_blue,
            theta=theta_values_blue,
            mode='markers',
            marker=dict(size=3, color='blue'),
            name='angle path'
        )
        red_tip = go.Scatterpolar(
            r=[1],
            theta=[angle],
            mode='markers',
            marker=dict(size=10, color='red'),
            name='current direction'
        )
        green_target = go.Scatterpolar(
            r=[1],
            theta=[target_angle],
            mode='markers',
            marker=dict(size=10, color='green'),
            name='target direction'
        )
        return {
            'data': [blue_dots, red_tip, green_target],
            'layout': go.Layout(
                polar=dict(
                    radialaxis=dict(visible=False),
                    angularaxis=dict(
                        direction='clockwise',
                        rotation=90,
                        tickmode='array',
                        tickvals=[0, 90, 180, 270],
                        ticktext=['0°', '90°', '270°']
                    )
                ),
                showlegend=True,
                title='현재 전차 각도 (나침반)'
            )
        }

    @app.callback(
        Output('path-obstacle-graph', 'figure'),
        Input('interval', 'n_intervals')
    )
    def update_path_obstacle_graph(n):
        with shared_lock:
            if 'pre_playerPos' not in shared or not all(key in shared['pre_playerPos'] for key in ['x', 'z']):
                logger.warning("pre_playerPos not properly initialized, using default values")
                current_pos = (0, 0)
            else:
                current_pos = (shared['pre_playerPos']['x'], shared['pre_playerPos']['z'])
            destination = shared.get('destination', None)
            obstacles = shared.get('obstacles', [])[:GRAPH_CONFIG['max_obstacles']]
            path = shared.get('path', [])[:GRAPH_CONFIG['max_path_points']]
            nearest_point = shared.get('nearest_point', None)
            map_points = shared.get('map_points', None)
            rddf_data = shared.get('rddf_data', [])

        data = [
            go.Scatter(
                x=[current_pos[0]], y=[current_pos[1]],
                mode='markers', marker=dict(size=10, color='blue'),
                name='현재 위치'
            )
        ]

        if destination:
            dest_x, dest_y, dest_z = destination
            data.append(go.Scatter(
                x=[dest_x], y=[dest_z],
                mode='markers', marker=dict(size=10, color='green'),
                name='목표'
            ))

        if path:
            path_x, path_z = zip(*path)
            data.append(go.Scatter(
                x=path_x, y=path_z,
                mode='lines+markers', line=dict(color='black', dash='dash'),
                name='경로'
            ))

        if map_points is not None:
            data.append(go.Scatter(
                x=map_points[:, 0], y=map_points[:, 1],
                mode='lines', line=dict(color='gray', width=1),
                name='지도 경로'
            ))

        if nearest_point:
            data.append(go.Scatter(
                x=[nearest_point[0]], y=[nearest_point[1]],
                mode='markers', marker=dict(size=10, color='orange'),
                name='가장 가까운 점'
            ))

        if rddf_data:
            df_rddf = pd.DataFrame(rddf_data, columns=['x', 'z', 'y', 'speed'])
            rddf_x = df_rddf['x'].values
            rddf_z = df_rddf['z'].values
            data.append(go.Scatter(
                x=rddf_x, y=rddf_z,
                mode='lines+markers', line=dict(color='blue', width=2),
                name='RDDF 궤적'
            ))

        for i, (obs_x, obs_z) in enumerate(obstacles):
            data.append(go.Scatter(
                x=[obs_x], y=[obs_z],
                mode='markers', marker=dict(size=15, color='red', symbol='x'),
                name=f'장애물 {i+1}'
            ))

        logger.debug("Updating path-obstacle graph with RDDF trajectory")
        return {
            'data': data,
            'layout': go.Layout(
                xaxis=dict(title='X 좌표 (m)', range=[50, 250]),
                yaxis=dict(title='Z 좌표 (m)', range=[25, 225]),
                title='경로 및 장애물 시각화 (RDDF 궤적 포함)',
                showlegend=True
            )
        }

    @app.callback(
        Output('error-distance-graph', 'figure'),
        Input('interval', 'n_intervals')
    )
    def update_error_graph(n):
        with shared_lock:
            error_distance = shared.get('error_distance', 0.0)
        return {
            'data': [go.Scatter(y=[error_distance], mode='markers', name='오차')],
            'layout': go.Layout(
                xaxis=dict(title='시간 (포인트)'),
                yaxis=dict(title='오차 거리 (m)', range=[0, 5]),
                title='위치 오차 시각화'
            )
        }

    @app.callback(
        Output('target-speed-display', 'children'),
        Input('target-speed-slider', 'value')
    )
    def update_target_speed_display(val):
        with shared_lock:
            if shared.get('error_distance', 0.0) < 0.5:
                shared['tank_tar_vel_kh'] = 0
                logger.info("Destination reached, setting target speed to 0 km/h")
            else:
                shared['tank_tar_vel_kh'] = val
            logger.info(f"Target speed updated: {shared['tank_tar_vel_kh']} km/h (Dash)")
        return f"현재 타겟 속도: {shared['tank_tar_vel_kh']} km/h"

    @app.callback(
        Output('target-angle-display', 'children'),
        Input('target-angle-slider', 'value')
    )
    def update_target_angle_display(angle):
        with shared_lock:
            shared['tank_tar_yaw_deg'] = angle
            logger.info(f"Target angle updated: {angle}° (Dash)")
        return f"현재 타겟 각도: {angle}°"

    @app.callback(
        Output('pid-display', 'children'),
        [Input('input-kp', 'value'),
         Input('input-ki', 'value'),
         Input('input-kd', 'value')]
    )
    def update_pid_values(kp, ki, kd):
        with shared_lock:
            shared['vel_pid']['kp'] = max(0, kp) if kp is not None else PID_CONFIG['kp']
            shared['vel_pid']['ki'] = max(0, ki) if ki is not None else PID_CONFIG['ki']
            shared['vel_pid']['kd'] = max(0, kd) if kd is not None else PID_CONFIG['kd']
        logger.info(f"Velocity PID updated: Kp={shared['vel_pid']['kp']}, Ki={shared['vel_pid']['ki']}, Kd={shared['vel_pid']['kd']}")
        return f"속도 PID 값 - Kp: {shared['vel_pid']['kp']}, Ki: {shared['vel_pid']['ki']}, Kd: {shared['vel_pid']['kd']}"

    @app.callback(
        Output('steer-pid-display', 'children'),
        [Input('steer-kp', 'value'),
         Input('steer-ki', 'value'),
         Input('steer-kd', 'value')]
    )
    def update_yaw_pid(kp, ki, kd):
        with shared_lock:
            shared['steer_pid']['kp'] = max(0, kp) if kp is not None else PID_CONFIG_DEG['kp']
            shared['steer_pid']['ki'] = max(0, ki) if ki is not None else PID_CONFIG_DEG['ki']
            shared['steer_pid']['kd'] = max(0, kd) if kd is not None else PID_CONFIG_DEG['kd']
        logger.info(f"Steering PID updated: Kp={shared['steer_pid']['kp']}, Ki={shared['steer_pid']['ki']}, Kd={shared['steer_pid']['kd']}")
        return f"조향 PID 값 - Kp: {shared['steer_pid']['kp']}, Ki: {shared['steer_pid']['ki']}, Kd: {shared['steer_pid']['kd']}"

    @app.callback(
        Output('rddf-speed-graph', 'figure'),
        Input('interval', 'n_intervals')
    )
    def update_rddf_speed_graph(n):
        with shared_lock:
            rddf_data = shared.get('rddf_data', [])
            if rddf_data:
                df_rddf = pd.DataFrame(rddf_data, columns=['x', 'z', 'y', 'speed'])
                logger.info(f"RDDF data loaded for speed graph from SHARED: {len(df_rddf)} rows")
                speeds = df_rddf['speed'].values[-GRAPH_CONFIG['max_points']:] * 3.6
            else:
                logger.warning("No RDDF data available in SHARED")
                speeds = []
        return {
            'data': [go.Scatter(
                y=speeds,
                mode='lines+markers',
                line=dict(color='orange', width=2),
                marker=dict(size=5),
                name='속도'
            )],
            'layout': go.Layout(
                xaxis=dict(
                    title='시간 (포인트)',
                    range=[max(0, len(speeds) - GRAPH_CONFIG['max_points']), len(speeds)]
                ),
                yaxis=dict(title='속도 (km/h)', range=[0, 108]),
                title='RDDF 속도 변화',
                showlegend=True
            )
        }

    return app

def run_dash():
    create_dash_app().run(port=SERVER_CONFIG['dash_port'], debug=False, use_reloader=False)