import csv
from datetime import datetime

def save_device_data_to_csv(device_name, time_buffer, as_polar_buffers, ang_acc_polar_buffers, filename):
    with open(filename, mode='a', newline='') as file:  # 使用 'a' 模式以附加方式打開文件
        writer = csv.writer(file)
        # 檢查文件是否為空，若是空的則寫入表頭
        if file.tell() == 0:
            # 標頭("時間戳"，"設備名稱"，"角速度值"，"角速度的θ"，"角速度的φ"，"角加速度值"，"角加速度的θ"，"角加速度的φ")
            writer.writerow(["timestamp", "device", "as_magnitude", "as_theta", "as_phi", "ang_acc_magnitude", "ang_acc_theta", "ang_acc_phi"])

        # 寫入設備數據
        for i in range(len(time_buffer)):
            readable_time = datetime.fromtimestamp(time_buffer[i])
            writer.writerow([
                readable_time,
                device_name,
                as_polar_buffers['Magnitude'][i],
                as_polar_buffers['Theta'][i],
                as_polar_buffers['Phi'][i],
                ang_acc_polar_buffers['Magnitude'][i],
                ang_acc_polar_buffers['Theta'][i],
                ang_acc_polar_buffers['Phi'][i]
            ])
# 將 Device1 和 Device2 的數據分別保存到各自的 CSV 文件中。
def save_data_to_csv():
    """
    參數:
      device_name : 設備名稱，例如 "Device1" 或 "Device2"。
      time_buffer : 包含時間戳的緩衝區。
      as_polar_buffers : 包含角速度（極座標）的緩衝區字典，鍵包括 'Magnitude'、'Theta'、'Phi'。
      ang_acc_polar_buffers : 包含角加速度（極座標）的緩衝區字典，鍵包括 'Magnitude'、'Theta'、'Phi'。
      filename : 要保存數據的 CSV 文件名稱。
    """
    from config import time_buffer_1, as_polar_buffers_1, ang_acc_polar_buffers_1
    from config import time_buffer_2, as_polar_buffers_2, ang_acc_polar_buffers_2
    
    save_device_data_to_csv("Device1", time_buffer_1, as_polar_buffers_1, ang_acc_polar_buffers_1, "device1_data.csv")
    save_device_data_to_csv("Device2", time_buffer_2, as_polar_buffers_2, ang_acc_polar_buffers_2, "device2_data.csv")
