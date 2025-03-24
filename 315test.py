import matplotlib                           #用於創建圖表和可視化數據
# 若你在終端執行且想強制 Qt5，可解開下一行:
# matplotlib.use('Qt5Agg')

import matplotlib.pyplot as plt             #簡化圖表創建
import matplotlib.animation as animation    #用於動畫效果
import asyncio                              #支持異步編程
import nest_asyncio                         #允許嵌套的事件循環
import bleak                                #用於藍牙低功耗通信
import device_model                         #需自行確保有此類別
from datetime import datetime               #處理日期和時間
from collections import deque               #支持快速追加和彈出操作的雙端隊列
import threading                            #多線程編程
import math                                 #數學函數
import csv                                  #CSV 檔案讀取及寫入
import time                                 #時間函數

# 1) 設定 asyncio 與 nest_asyncio
nest_asyncio.apply()
asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

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

# 2) Device1: updateData1()
def updateData1(DeviceModel):
    global time_buffer_1, as_polar_buffers_1, ang_acc_polar_buffers_1, latest_data_1
    global last_timestamp_1, last_as_x_1, last_as_y_1, last_as_z_1
    global last_smoothed_as_x_1, last_smoothed_as_y_1, last_smoothed_as_z_1

    now = datetime.now()
    timestamp = now.timestamp()
    time_buffer_1.append(timestamp)

    # (1) 取得原始 LSB
    as_x_raw = DeviceModel.get("AsX") or 0
    as_y_raw = DeviceModel.get("AsY") or 0
    as_z_raw = DeviceModel.get("AsZ") or 0

    # (2) LSB → deg/s
    as_x_deg = as_x_raw * LSB_TO_DEG_PER_S
    as_y_deg = as_y_raw * LSB_TO_DEG_PER_S
    as_z_deg = as_z_raw * LSB_TO_DEG_PER_S

    # (3) deg/s → rad/s
    as_x = as_x_deg * math.pi / 180.0
    as_y = as_y_deg * math.pi / 180.0
    as_z = as_z_deg * math.pi / 180.0

    # (4) 對角速度做【指數平滑】
    if last_smoothed_as_x_1 is None:
        # 第一次就直接賦值
        last_smoothed_as_x_1 = as_x
        last_smoothed_as_y_1 = as_y
        last_smoothed_as_z_1 = as_z
    else:
        # EMA
        as_x = ALPHA * as_x + (1 - ALPHA) * last_smoothed_as_x_1
        as_y = ALPHA * as_y + (1 - ALPHA) * last_smoothed_as_y_1
        as_z = ALPHA * as_z + (1 - ALPHA) * last_smoothed_as_z_1

        last_smoothed_as_x_1 = as_x
        last_smoothed_as_y_1 = as_y
        last_smoothed_as_z_1 = as_z

    # (5) 角速度 (極座標)
    as_magnitude = math.sqrt(as_x**2 + as_y**2 + as_z**2)
    as_theta = math.atan2(as_y, as_x) if (as_x != 0 or as_y != 0) else 0
    as_phi = 0
    if as_magnitude != 0:
        z_ratio = max(min(as_z / as_magnitude, 1), -1)
        as_phi = math.acos(z_ratio)

    as_polar_buffers_1['Magnitude'].append(as_magnitude)
    as_polar_buffers_1['Theta'].append(as_theta)
    as_polar_buffers_1['Phi'].append(as_phi)

    # (6) 角加速度 = Δω / Δt
    if last_timestamp_1 is not None:
        dt = timestamp - last_timestamp_1
        if dt >= MIN_DT:
            # 正常計算
            ang_acc_x = (as_x - last_as_x_1) / dt
            ang_acc_y = (as_y - last_as_y_1) / dt
            ang_acc_z = (as_z - last_as_z_1) / dt

            ang_acc_magnitude = math.sqrt(ang_acc_x**2 + ang_acc_y**2 + ang_acc_z**2)
            ang_acc_theta = math.atan2(ang_acc_y, ang_acc_x) if (ang_acc_x != 0 or ang_acc_y != 0) else 0
            ang_acc_phi = 0
            if ang_acc_magnitude != 0:
                z_ratio = max(min(ang_acc_z / ang_acc_magnitude, 1), -1)
                ang_acc_phi = math.acos(z_ratio)

            ang_acc_polar_buffers_1['Magnitude'].append(ang_acc_magnitude)
            ang_acc_polar_buffers_1['Theta'].append(ang_acc_theta)
            ang_acc_polar_buffers_1['Phi'].append(ang_acc_phi)

            latest_data_1['AngAccMagnitude'] = ang_acc_magnitude
            latest_data_1['AngAccTheta'] = ang_acc_theta
            latest_data_1['AngAccPhi'] = ang_acc_phi
        else:
            # dt 太小 -> 略過
            ang_acc_polar_buffers_1['Magnitude'].append(0)
            ang_acc_polar_buffers_1['Theta'].append(0)
            ang_acc_polar_buffers_1['Phi'].append(0)
    else:
        # 第一次沒有舊值
        ang_acc_polar_buffers_1['Magnitude'].append(0)
        ang_acc_polar_buffers_1['Theta'].append(0)
        ang_acc_polar_buffers_1['Phi'].append(0)

    latest_data_1['AsMagnitude'] = as_magnitude
    latest_data_1['AsTheta'] = as_theta
    latest_data_1['AsPhi'] = as_phi

    last_timestamp_1 = timestamp
    last_as_x_1, last_as_y_1, last_as_z_1 = as_x, as_y, as_z

# 3) Device2: updateData2() (相同邏輯)
def updateData2(DeviceModel):
    global time_buffer_2, as_polar_buffers_2, ang_acc_polar_buffers_2, latest_data_2
    global last_timestamp_2, last_as_x_2, last_as_y_2, last_as_z_2
    global last_smoothed_as_x_2, last_smoothed_as_y_2, last_smoothed_as_z_2

    now = datetime.now()
    timestamp = now.timestamp()
    time_buffer_2.append(timestamp)

    as_x_raw = DeviceModel.get("AsX") or 0
    as_y_raw = DeviceModel.get("AsY") or 0
    as_z_raw = DeviceModel.get("AsZ") or 0

    as_x_deg = as_x_raw * LSB_TO_DEG_PER_S
    as_y_deg = as_y_raw * LSB_TO_DEG_PER_S
    as_z_deg = as_z_raw * LSB_TO_DEG_PER_S

    as_x = as_x_deg * math.pi / 180.0
    as_y = as_y_deg * math.pi / 180.0
    as_z = as_z_deg * math.pi / 180.0

    # EMA (Device2)
    if last_smoothed_as_x_2 is None:
        last_smoothed_as_x_2 = as_x
        last_smoothed_as_y_2 = as_y
        last_smoothed_as_z_2 = as_z
    else:
        as_x = ALPHA * as_x + (1 - ALPHA) * last_smoothed_as_x_2
        as_y = ALPHA * as_y + (1 - ALPHA) * last_smoothed_as_y_2
        as_z = ALPHA * as_z + (1 - ALPHA) * last_smoothed_as_z_2

        last_smoothed_as_x_2 = as_x
        last_smoothed_as_y_2 = as_y
        last_smoothed_as_z_2 = as_z

    as_magnitude = math.sqrt(as_x**2 + as_y**2 + as_z**2)
    as_theta = math.atan2(as_y, as_x) if (as_x != 0 or as_y != 0) else 0
    as_phi = 0
    if as_magnitude != 0:
        z_ratio = max(min(as_z / as_magnitude, 1), -1)
        as_phi = math.acos(z_ratio)

    as_polar_buffers_2['Magnitude'].append(as_magnitude)
    as_polar_buffers_2['Theta'].append(as_theta)
    as_polar_buffers_2['Phi'].append(as_phi)

    if last_timestamp_2 is not None:
        dt = timestamp - last_timestamp_2
        if dt >= MIN_DT:
            ang_acc_x = (as_x - last_as_x_2) / dt
            ang_acc_y = (as_y - last_as_y_2) / dt
            ang_acc_z = (as_z - last_as_z_2) / dt

            ang_acc_magnitude = math.sqrt(ang_acc_x**2 + ang_acc_y**2 + ang_acc_z**2)
            ang_acc_theta = math.atan2(ang_acc_y, ang_acc_x) if (ang_acc_x != 0 or ang_acc_y != 0) else 0
            ang_acc_phi = 0
            if ang_acc_magnitude != 0:
                z_ratio = max(min(ang_acc_z / ang_acc_magnitude, 1), -1)
                ang_acc_phi = math.acos(z_ratio)

            ang_acc_polar_buffers_2['Magnitude'].append(ang_acc_magnitude)
            ang_acc_polar_buffers_2['Theta'].append(ang_acc_theta)
            ang_acc_polar_buffers_2['Phi'].append(ang_acc_phi)

            latest_data_2['AngAccMagnitude'] = ang_acc_magnitude
            latest_data_2['AngAccTheta'] = ang_acc_theta
            latest_data_2['AngAccPhi'] = ang_acc_phi
        else:
            ang_acc_polar_buffers_2['Magnitude'].append(0)
            ang_acc_polar_buffers_2['Theta'].append(0)
            ang_acc_polar_buffers_2['Phi'].append(0)
    else:
        ang_acc_polar_buffers_2['Magnitude'].append(0)
        ang_acc_polar_buffers_2['Theta'].append(0)
        ang_acc_polar_buffers_2['Phi'].append(0)

    latest_data_2['AsMagnitude'] = as_magnitude
    latest_data_2['AsTheta'] = as_theta
    latest_data_2['AsPhi'] = as_phi

    last_timestamp_2 = timestamp
    last_as_x_2, last_as_y_2, last_as_z_2 = as_x, as_y, as_z

# 4) 持續掃描，直到找到 2 台
async def scan_until_2():
    while True:
        print("開始掃描 (10 秒) ...")
        try:
            devices = await bleak.BleakScanner.discover(timeout=10.0)
        except Exception as ex:
            print("掃描時出現錯誤:", ex)
            await asyncio.sleep(5)
            continue

        found = []
        for d in devices:
            # 假設只要名稱含 "WT" 就算符合 (可自行修改)
            if d.name and "WT" in d.name:
                found.append(d)

        if found:
            print("本次掃描到符合 'WT' 的裝置:")
            for idx, f in enumerate(found):
                print(f"  {idx+1}) {f.address} - {f.name}")

        if len(found) >= 2:
            dev1, dev2 = found[0], found[1]
            print(f"已找到 {len(found)} 台，取前兩台")
            print(f"Device1: {dev1.address} - {dev1.name}")
            print(f"Device2: {dev2.address} - {dev2.name}\n")
            return dev1, dev2
        else:
            print(f"目前只找到 {len(found)} 台 (需要>=2)，等待3秒後再掃描...\n")
            await asyncio.sleep(3)

#將裝置數據儲存成csv(裝置名稱， 時間， 角速度， 角加速度， csv檔名稱)
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
    save_device_data_to_csv("Device1", time_buffer_1, as_polar_buffers_1, ang_acc_polar_buffers_1, "device1_data.csv")
    save_device_data_to_csv("Device2", time_buffer_2, as_polar_buffers_2, ang_acc_polar_buffers_2, "device2_data.csv")

# 每 10 秒儲存一次csv
async def periodic_save(interval):
    while True:
        save_data_to_csv()
        await asyncio.sleep(interval)
# 主執行緒:負責掃描、初始化和運行兩個藍牙設備
async def main_coroutine():
    # 掃描直到找到兩個符合條件的設備
    dev1, dev2 = await scan_until_2()
    # 創建兩個設備模型對象，並將其與對應的更新函數關聯
    device1 = device_model.DeviceModel("MyBle5.0_Device1", dev1, updateData1)
    device2 = device_model.DeviceModel("MyBle5.0_Device2", dev2, updateData2)
    # 定義運行設備1的函數
    def run_device1():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(device1.openDevice())
        except Exception as ex:
            print(f"run_device1 錯誤: {ex}")
    # 定義運行設備2的函數
    def run_device2():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(device2.openDevice())
        except Exception as ex:
            print(f"run_device2 錯誤: {ex}")

     # 使用多線程方式運行設備1和設備2的函數
    threading.Thread(target=run_device1, daemon=True).start()
    threading.Thread(target=run_device2, daemon=True).start()

    # 啟動定時保存任務
    asyncio.create_task(periodic_save(10))

    while True:
        await asyncio.sleep(1)
# 負責啟動藍牙設備的主協程
def start_ble():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main_coroutine())


# 5) Matplotlib 動態繪圖
plt.rcParams['font.size'] = 14  
fig, (ax_as, ax_acc) = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
plt.subplots_adjust(right=0.8, hspace=0.3)

# 上圖：角速度
ax_as.set_title("Angular Velocity Magnitude vs. Time (rad/s)", fontsize=14)
ax_as.set_ylabel("As Mag (rad/s)", fontsize=12)
ax_as.grid(True)
line_as1, = ax_as.plot([], [], 'r-', lw=2, label='Device1 As')
line_as2, = ax_as.plot([], [], 'b-', lw=2, label='Device2 As')
ax_as.legend(loc='upper left')

text_as1 = ax_as.text(1.02, 0.7, "", transform=ax_as.transAxes,
                      color='red', ha='left', va='center', fontsize=12)
text_as2 = ax_as.text(1.02, 0.3, "", transform=ax_as.transAxes,
                      color='blue', ha='left', va='center', fontsize=12)

# 下圖：角加速度
ax_acc.set_title("Angular Acceleration Magnitude vs. Time (rad/s²)", fontsize=14)
ax_acc.set_ylabel("AngAcc Mag (rad/s²)", fontsize=12)
ax_acc.set_xlabel("Time (s)", fontsize=12)
ax_acc.grid(True)
line_acc1, = ax_acc.plot([], [], 'r-', lw=2, label='Device1 Acc')
line_acc2, = ax_acc.plot([], [], 'b-', lw=2, label='Device2 Acc')
ax_acc.legend(loc='upper left')

text_acc1 = ax_acc.text(1.02, 0.7, "", transform=ax_acc.transAxes,
                        color='red', ha='left', va='center', fontsize=12)
text_acc2 = ax_acc.text(1.02, 0.3, "", transform=ax_acc.transAxes,
                        color='blue', ha='left', va='center', fontsize=12)

def update_plot(frame):
    # Device1
    t1 = list(time_buffer_1)
    as1 = list(as_polar_buffers_1['Magnitude'])
    acc1 = list(ang_acc_polar_buffers_1['Magnitude'])

    if t1 and as1:
        line_as1.set_data(t1, as1)
    if t1 and acc1:
        line_acc1.set_data(t1, acc1)

    # Device2
    t2 = list(time_buffer_2)
    as2 = list(as_polar_buffers_2['Magnitude'])
    acc2 = list(ang_acc_polar_buffers_2['Magnitude'])

    if t2 and as2:
        line_as2.set_data(t2, as2)
    if t2 and acc2:
        line_acc2.set_data(t2, acc2)

    # 動態調整 X 軸範圍: 只顯示最近10秒
    all_times = t1 + t2
    if all_times:
        t_max = max(all_times)
        t_min = max(0, t_max - 10)
        ax_as.set_xlim(t_min, t_max + 0.5)
        ax_acc.set_xlim(ax_as.get_xlim())

    # 動態調整 Y 軸 (角速度)
    all_as = as1 + as2
    if all_as:
        y_min_as = min(all_as)
        y_max_as = max(all_as)
        padding_as = (y_max_as - y_min_as) * 0.1 if (y_max_as - y_min_as) else 1
        ax_as.set_ylim(y_min_as - padding_as, y_max_as + padding_as)

    # 動態調整 Y 軸 (角加速度)
    all_acc = acc1 + acc2
    if all_acc:
        y_min_acc = min(all_acc)
        y_max_acc = max(all_acc)
        padding_acc = (y_max_acc - y_min_acc) * 0.1 if (y_max_acc - y_min_acc) else 1
        ax_acc.set_ylim(y_min_acc - padding_acc, y_max_acc + padding_acc)

    # 更新右側文字 (Device1)
    as_m_1 = as1[-1] if as1 else 0
    as_t_1 = as_polar_buffers_1['Theta'][-1] if as_polar_buffers_1['Theta'] else 0
    as_p_1 = as_polar_buffers_1['Phi'][-1]   if as_polar_buffers_1['Phi'] else 0
    acc_m_1 = acc1[-1] if acc1 else 0
    acc_t_1 = ang_acc_polar_buffers_1['Theta'][-1] if ang_acc_polar_buffers_1['Theta'] else 0
    acc_p_1 = ang_acc_polar_buffers_1['Phi'][-1]   if ang_acc_polar_buffers_1['Phi'] else 0

    text_as1.set_text(
        f"[Dev1]\nM: {as_m_1:.2f}\nθ: {math.degrees(as_t_1):.2f}°\nφ: {math.degrees(as_p_1):.2f}°"
    )
    text_acc1.set_text(
        f"[Dev1]\nM: {acc_m_1:.2f}\nθ: {math.degrees(acc_t_1):.2f}°\nφ: {math.degrees(acc_p_1):.2f}°"
    )

    # 更新右側文字 (Device2)
    as_m_2 = as2[-1] if as2 else 0
    as_t_2 = as_polar_buffers_2['Theta'][-1] if as_polar_buffers_2['Theta'] else 0
    as_p_2 = as_polar_buffers_2['Phi'][-1]   if as_polar_buffers_2['Phi'] else 0
    acc_m_2 = acc2[-1] if acc2 else 0
    acc_t_2 = ang_acc_polar_buffers_2['Theta'][-1] if ang_acc_polar_buffers_2['Theta'] else 0
    acc_p_2 = ang_acc_polar_buffers_2['Phi'][-1]   if ang_acc_polar_buffers_2['Phi'] else 0

    text_as2.set_text(
        f"[Dev2]\nM: {as_m_2:.2f}\nθ: {math.degrees(as_t_2):.2f}°\nφ: {math.degrees(as_p_2):.2f}°"
    )
    text_acc2.set_text(
        f"[Dev2]\nM: {acc_m_2:.2f}\nθ: {math.degrees(acc_t_2):.2f}°\nφ: {math.degrees(acc_p_2):.2f}°"
    )

    return (line_as1, line_as2, line_acc1, line_acc2,
            text_as1, text_as2, text_acc1, text_acc2)
#更新頻率100ms,blit=True(只更新有變動的數據)
ani = animation.FuncAnimation(fig, update_plot, interval=100, blit=True)


if __name__ == '__main__':
    ble_thread = threading.Thread(target=start_ble, daemon=True)
    ble_thread.start()
    plt.show()
