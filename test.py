from device import *
from data_processing import *
from config import *
from plotting import *
import asyncio
import threading
import device_model
import nest_asyncio                         #允許嵌套的事件循環

nest_asyncio.apply()
asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

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

def thread_job():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main_coroutine())

# 在main中新增顯示極座標圖的邏輯
if __name__ == '__main__':
    ble_thread = threading.Thread(target=thread_job, daemon=True)
    ble_thread.start()
    plt.show()