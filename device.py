import asyncio
import bleak
from datetime import datetime
from config import *

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

# 掃描裝置
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