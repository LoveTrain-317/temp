from config import *
import matplotlib.pyplot as plt             #簡化圖表創建
import matplotlib.animation as animation    #用於動畫效果

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

text_as1 = ax_as.text(0, 0.5, "", transform=ax_as.transAxes,
                      color='red', ha='left', va='center', fontsize=12)
text_as2 = ax_as.text(0.1, 0.5, "", transform=ax_as.transAxes,
                      color='blue', ha='left', va='center', fontsize=12)

# 下圖：角加速度
ax_acc.set_title("Angular Acceleration Magnitude vs. Time (rad/s²)", fontsize=14)
ax_acc.set_ylabel("AngAcc Mag (rad/s²)", fontsize=12)
ax_acc.set_xlabel("Time (s)", fontsize=12)
ax_acc.grid(True)
line_acc1, = ax_acc.plot([], [], 'r-', lw=2, label='Device1 Acc')
line_acc2, = ax_acc.plot([], [], 'b-', lw=2, label='Device2 Acc')
ax_acc.legend(loc='upper left')

text_acc1 = ax_acc.text(0, 0.5, "", transform=ax_acc.transAxes,
                        color='red', ha='left', va='center', fontsize=12)
text_acc2 = ax_acc.text(0.1, 0.5, "", transform=ax_acc.transAxes,
                        color='blue', ha='left', va='center', fontsize=12)

# 新增極座標圖的設置
fig_polar, (ax_polar_as, ax_polar_acc) = plt.subplots(2, 1, subplot_kw={'projection': 'polar'},
                                                       figsize=(9, 7), sharex=True)
plt.subplots_adjust(right=0.8, hspace=0.3)

# 上圖：角速度的極座標圖
ax_polar_as.set_title("Angular Velocity Polar Plot", fontsize=14)
line_polar_as1, = ax_polar_as.plot([], [], 'ro-', lw=2, label='Device1 As')
line_polar_as2, = ax_polar_as.plot([], [], 'bo-', lw=2, label='Device2 As')
ax_polar_as.legend(loc='upper left', bbox_to_anchor=(1.1, 1.05))

text_polar_as1 = ax_polar_as.text(0, 0.5, "", transform=ax_polar_as.transAxes, color='red',
                                   ha='left', va='center', fontsize=10)
text_polar_as2 = ax_polar_as.text(0, 0.4, "", transform=ax_polar_as.transAxes, color='blue',
                                   ha='left', va='center', fontsize=10)


# 下圖：角加速度的極座標圖
ax_polar_acc.set_title("Angular Acceleration Polar Plot", fontsize=14)
line_polar_acc1, = ax_polar_acc.plot([], [], 'ro-', lw=2, label='Device1 Acc')
line_polar_acc2, = ax_polar_acc.plot([], [], 'bo-', lw=2, label='Device2 Acc')
ax_polar_acc.legend(loc='upper left', bbox_to_anchor=(1.1, 1.05))

text_polar_acc1 = ax_polar_acc.text(0, 0.5, "", transform=ax_polar_acc.transAxes, color='red',
                                     ha='left', va='center', fontsize=10)
text_polar_acc2 = ax_polar_acc.text(0, 0.4, "", transform=ax_polar_acc.transAxes, color='blue',
                                     ha='left', va='center', fontsize=10)


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

def update_polar_plot(frame):
    # Device1 角速度
    theta_as1 = list(as_polar_buffers_1['Theta'])
    r_as1 = list(as_polar_buffers_1['Magnitude'])

    if theta_as1 and r_as1:
        line_polar_as1.set_data([theta_as1[-1]], [r_as1[-1]])  # 只顯示當前點
        # 更新文本標籤
        text_polar_as1.set_text(f"As: θ={math.degrees(theta_as1[-1]):.2f}°, r={r_as1[-1]:.2f}")

    # Device2 角速度
    theta_as2 = list(as_polar_buffers_2['Theta'])
    r_as2 = list(as_polar_buffers_2['Magnitude'])

    if theta_as2 and r_as2:
        line_polar_as2.set_data([theta_as2[-1]], [r_as2[-1]])  # 只顯示當前點
        # 更新文本標籤
        text_polar_as2.set_text(f"As: θ={math.degrees(theta_as2[-1]):.2f}°, r={r_as2[-1]:.2f}")

    # Device1 角加速度
    theta_acc1 = list(ang_acc_polar_buffers_1['Theta'])
    r_acc1 = list(ang_acc_polar_buffers_1['Magnitude'])

    if theta_acc1 and r_acc1:
        line_polar_acc1.set_data([theta_acc1[-1]], [r_acc1[-1]])  # 只顯示當前點
        # 更新文本標籤
        text_polar_acc1.set_text(f"Acc: θ={math.degrees(theta_acc1[-1]):.2f}°, r={r_acc1[-1]:.2f}")

    # Device2 角加速度
    theta_acc2 = list(ang_acc_polar_buffers_2['Theta'])
    r_acc2 = list(ang_acc_polar_buffers_2['Magnitude'])

    if theta_acc2 and r_acc2:
        line_polar_acc2.set_data([theta_acc2[-1]], [r_acc2[-1]])  # 只顯示當前點
        # 更新文本標籤
        text_polar_acc2.set_text(f"Acc: θ={math.degrees(theta_acc2[-1]):.2f}°, r={r_acc2[-1]:.2f}")

    return (line_polar_as1, line_polar_as2, line_polar_acc1, line_polar_acc2,
            text_polar_as1, text_polar_as2, text_polar_acc1, text_polar_acc2)

# 更新頻率100ms,blit=True(只更新有變動的數據)
ani_polar = animation.FuncAnimation(fig_polar, update_polar_plot, interval=100, blit=True)
