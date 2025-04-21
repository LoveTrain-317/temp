import math
from collections import deque

# ============== 全域參數設定 ==============
max_points = 200

# 指數平滑係數 (0 < ALPHA < 1，越小越平滑)
ALPHA = 0.2  
# 若 dt < MIN_DT，就忽略本次角加速度
MIN_DT = 0.01  

# ==========< Device1 的全域變數 >==========
time_buffer_1 = deque(maxlen=max_points)
as_polar_buffers_1 = {
    'Magnitude': deque(maxlen=max_points),
    'Theta': deque(maxlen=max_points),
    'Phi': deque(maxlen=max_points)
}
ang_acc_polar_buffers_1 = {
    'Magnitude': deque(maxlen=max_points),
    'Theta': deque(maxlen=max_points),
    'Phi': deque(maxlen=max_points)
}
latest_data_1 = {
    'AsMagnitude': 0, 'AsTheta': 0, 'AsPhi': 0,
    'AngAccMagnitude': 0, 'AngAccTheta': 0, 'AngAccPhi': 0
}
last_timestamp_1 = None
last_as_x_1 = 0
last_as_y_1 = 0
last_as_z_1 = 0

# Exponential Moving Average 用
last_smoothed_as_x_1 = None
last_smoothed_as_y_1 = None
last_smoothed_as_z_1 = None

# ==========< Device2 的全域變數 >==========
time_buffer_2 = deque(maxlen=max_points)
as_polar_buffers_2 = {
    'Magnitude': deque(maxlen=max_points),
    'Theta': deque(maxlen=max_points),
    'Phi': deque(maxlen=max_points)
}
ang_acc_polar_buffers_2 = {
    'Magnitude': deque(maxlen=max_points),
    'Theta': deque(maxlen=max_points),
    'Phi': deque(maxlen=max_points)
}
latest_data_2 = {
    'AsMagnitude': 0, 'AsTheta': 0, 'AsPhi': 0,
    'AngAccMagnitude': 0, 'AngAccTheta': 0, 'AngAccPhi': 0
}
last_timestamp_2 = None
last_as_x_2 = 0
last_as_y_2 = 0
last_as_z_2 = 0

last_smoothed_as_x_2 = None
last_smoothed_as_y_2 = None
last_smoothed_as_z_2 = None

# 假設使用 ±2000 °/s 檔位, 1 LSB = 0.061 °/s
LSB_TO_DEG_PER_S = 0.061