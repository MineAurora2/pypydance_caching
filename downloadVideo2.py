import random
import requests
import os
import time
from tqdm import tqdm

# 视频缓存目录
VIDEO_CACHE_DIR = './video_cache'
# 代理服务器地址
PROXY_SERVER = 'http://127.0.0.1:7890'
# 代理组合
proxies = {'http': PROXY_SERVER, 'https': PROXY_SERVER}
# 创建Session实例
session = requests.Session()
session.proxies = proxies

# 确保视频缓存目录存在
if not os.path.exists(VIDEO_CACHE_DIR):
    os.makedirs(VIDEO_CACHE_DIR)


def download_video(video_id, retry=3, delay=1):
    video_path = os.path.join(VIDEO_CACHE_DIR, f'{video_id}.mp4')
    if os.path.exists(video_path):
        print(f"{video_id}-视频已被下载，跳过下载")
        return
    print(f"视频id: {video_id} 没有下载，下载中...")
    video_url = f'http://jd.pypy.moe/api/v1/videos/{video_id}.mp4'

    # 请求随机延迟
    y = float(10)
    time.sleep((random.random() * y) + 5)

    start_time = time.time()
    bytes_downloaded = 0
    low_speed_duration = 120  # 2分钟低速度阈值
    min_speed_bytes_per_second = 125000  # 1Mbps的字节数

    while retry > 0:
        try:
            with session.get(video_url, stream=True) as response:
                if response.status_code == 200:
                    total_size_in_bytes = int(response.headers.get('content-length', 0))
                    progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True,
                                        desc=f"Downloading video {video_id}")
                    with open(video_path, 'wb') as video_file:
                        for data in response.iter_content(chunk_size=1024):
                            now = time.time()
                            bytes_downloaded += len(data)
                            current_speed = bytes_downloaded / (now - start_time)
                            if current_speed < min_speed_bytes_per_second and (now - start_time) > low_speed_duration:
                                print(f"\n下载速度低于1Mbps超过2分钟，重新下载视频id: {video_id}")
                                progress_bar.close()
                                video_file.close()
                                os.remove(video_path)
                                time.sleep(delay)
                                download_video(video_id, retry - 1, delay * 2)  # 递归调用以重新下载
                                return
                            video_file.write(data)
                            progress_bar.update(len(data))
                    print(f"\n视频id: {video_id} 下载成功")
                    progress_bar.close()
                    break
                else:
                    print(f"\n视频id: {video_id} 下载失败，状态码：{response.status_code}")
                    progress_bar.close()
        except Exception as e:
            print(f"\n视频id: {video_id} 下载异常，错误：{e}")
        time.sleep(delay)  # 增加延时以减少请求频率
        retry -= 1
        delay *= 2  # 指数退避策略
    else:
        print(f"\n视频id: {video_id} 多次尝试下载失败")


def batch_download_videos(start_id, end_id):
    for video_id in range(start_id, end_id + 1):
        download_video(video_id)


# 示例用法：
batch_download_videos(1000, 3752)  # 下载起始到结束id的视频
