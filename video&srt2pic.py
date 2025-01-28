import os
import pysrt
import pandas as pd
import threading
from moviepy import VideoFileClip
from tqdm import tqdm

def process_id(id:str,pbar:tqdm=None)->None:
    subs = pysrt.open('s'+id+'.srt', encoding='utf-8-sig')
    video = VideoFileClip(id+'.mp4')
    folder_path="jpg_"+id
    df=pd.DataFrame(columns=['path','content'])
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    cnt=0
    for sub in subs:
        file_path="{:}\\{:03}.jpg".format(folder_path,sub.index)
        mid_time = (sub.start.ordinal + sub.end.ordinal) / 2 / 1000
        video.save_frame(file_path, t=mid_time)
        df.loc[cnt]=[file_path,sub.text]
        cnt+=1
        pbar.update()
        # if cnt==10:
        #     break
    
    # print(df)
    df.to_csv(folder_path+"\\index.csv",escapechar='|',encoding='utf-8')

def item_cnt(tasks:list[str])->int:
    sum=0
    for t in tasks:
        sub = pysrt.open('s'+t+'.srt', encoding='utf-8-sig')
        sum+=len(sub)
    return sum

if __name__=="__main__":
    tasks=["{:02}".format(i+1) for i in range(13)]
    cnt=item_cnt(tasks)
    print("total items:%i"%cnt)
    pbar=tqdm(total=cnt,ncols=100)

    thread_list=[threading.Thread(target=process_id,args=(task,pbar)) for task in tasks]
    for i in thread_list:
        i.start()
    for i in thread_list:
        i.join()
    # process_id("01",pbar)