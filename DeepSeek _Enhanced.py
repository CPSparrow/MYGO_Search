# DeepSeek修改的版本

import os
import pysrt
import pandas as pd
from moviepy import VideoFileClip
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Manager
import time

def process_id(id: str, progress_queue) -> None:
    try:
        # 读取字幕文件
        subs = pysrt.open(f's{id}.srt', encoding='utf-8-sig')
        # 预先加载视频对象
        video = VideoFileClip(f'{id}.mp4')
        folder_path = f'jpg_{id}'
        os.makedirs(folder_path, exist_ok=True)

        # 使用列表暂存数据，最后批量写入
        rows = []
        for sub in subs:
            mid_time = (sub.start.ordinal + sub.end.ordinal) / 2 / 1000
            # 使用跨平台路径拼接
            file_path = os.path.join(folder_path, f"{sub.index:03}.jpg")
            # 提取并保存帧
            video.save_frame(file_path, t=mid_time)
            rows.append({'path': file_path, 'content': sub.text})
            # 发送进度更新
            progress_queue.put(1)

        # 批量生成DataFrame并保存
        df = pd.DataFrame(rows)
        df.to_csv(os.path.join(folder_path, 'index.csv'),
                  escapechar='|',
                  encoding='utf-8',
                  index=False)
        # 显式释放视频资源
        video.close()
    except Exception as e:
        print(f"Error processing {id}: {str(e)}")

def get_task_counts(tasks):
    """预计算总任务数避免重复IO"""
    counts = {}
    for t in tasks:
        subs = pysrt.open(f's{t}.srt', encoding='utf-8-sig')
        counts[t] = len(subs)
    return counts

if __name__ == "__main__":
    # 初始化任务列表
    tasks = [f"{i+1:02}" for i in range(13)]

    # 预加载所有字幕文件统计总数
    task_counts = get_task_counts(tasks)
    total = sum(task_counts.values())

    # 使用多进程共享队列管理进度
    with Manager() as manager:
        progress_queue = manager.Queue()
        pbar = tqdm(total=total, ncols=100, desc="Processing")

        # 根据CPU核心数限制进程并发数
        max_workers = min(os.cpu_count(), len(tasks))
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务到进程池
            futures = [executor.submit(process_id, task, progress_queue)
                       for task in tasks]

            # 进度更新监听循环
            processed = 0
            while processed < total:
                # 批量获取进度更新减少IPC开销
                while not progress_queue.empty():
                    progress_queue.get()
                    processed += 1
                    pbar.update(1)
                # 检查剩余任务状态
                if all(f.done() for f in futures):
                    break
                time.sleep(0.1)  # 降低CPU占用

            # 清理未完成的进度
            while not progress_queue.empty():
                progress_queue.get()
                pbar.update(1)

            # 确保所有任务完成
            for future in futures:
                future.result()

        pbar.close()