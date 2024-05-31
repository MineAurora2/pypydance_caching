# 安装依赖命令
# pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
# https://jd.pypy.moe/api/v2/songs
# http://jd.pypy.moe/api/v1/videos/3451.mp4
# 视频oss storage-cf.llss.io

from flask import Flask, request, send_file, Response
import requests
import os
import logging

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)
# 禁用控制台消息
app.debug = False

# 视频缓存目录
VIDEO_CACHE_DIR = './video_cache'
# 代理服务器地址
PROXY_SERVER = 'http://127.0.0.1:7890'
# 原始服务器地址，所有未被拦截的请求将转发到这里
ORIGINAL_SERVER = 'https://jd.pypy.moe'
# 代理组合
proxies = {'http': PROXY_SERVER, 'https': PROXY_SERVER}

# 确保视频缓存目录存在
if not os.path.exists(VIDEO_CACHE_DIR):
    os.makedirs(VIDEO_CACHE_DIR)

# 记录上一个视频id
temp_video_id = "0"

# 获取指定路径的文件夹大小（单位：GB）
def get_doc_real_size(p_doc):
    size = 0.0
    for root, dirs, files in os.walk(p_doc):
        size += sum([os.path.getsize(os.path.join(root, file)) for file in files])
    size = round(size/1024/1024/1024, 2)
    return size


@app.route('/api/v1/videos/<video_id>.mp4')
def get_video(video_id):
    # 检查视频是否已经被缓存
    video_path = os.path.join(VIDEO_CACHE_DIR, f'{video_id}.mp4')
    if not os.path.exists(video_path):
        print(f"{video_id}-视频没有缓存，下载中...")
        # 如果没有缓存，则下载视频
        video_url = f'http://jd.pypy.moe/api/v1/videos/{video_id}.mp4'
        response = requests.get(video_url, proxies=proxies)
        if response.status_code == 200:
            # 保存视频到缓存目录
            with open(video_path, 'wb') as video_file:
                video_file.write(response.content)
            print(f"{video_id}-视频下载成功")
        else:
            return "视频下载失败", 500

    # 从缓存目录返回视频
    # print("视频从缓存中加载成功")
    # 校验判断是否显示过
    global temp_video_id
    if temp_video_id != video_id:
        temp_video_id = video_id

        # 获取视频大小
        stats = os.stat(video_path)
        print(f"从缓存中加载视频ID: {video_id} (大小: {'%.2f' % (stats.st_size / 1048576)} Mb)")

        # 获取视频文件夹大小与数量
        files = os.listdir(VIDEO_CACHE_DIR)  # 读入文件夹
        video_path_num_mp4 = len(files)  # 统计文件夹中的文件个数
        video_path_size = get_doc_real_size(VIDEO_CACHE_DIR)
        print(f"当前缓存文件夹情况: 视频数量-{video_path_num_mp4}个,已缓存大小-{'%.2f' % video_path_size}Gb")
        print()

    return send_file(video_path)


@app.route('/<path:path>')
def proxy(path):
    print(f"加载url: {ORIGINAL_SERVER}/{path}")
    original_url = f'{ORIGINAL_SERVER}/{path}'
    query_params = request.query_string.decode("utf-8")
    if query_params:
        original_url += f'?{query_params}'

    # 根据原始请求方法动态选择requests方法
    method = request.method.lower()
    req_func = getattr(requests, method, None)
    if not req_func:
        return "不支持的方法", 405

    # 转发请求到原始服务器（包括数据和头部，去除host头部避免问题）
    headers = {key: value for key, value in request.headers if key != 'Host'}
    response = req_func(original_url, headers=headers, data=request.data, params=request.args, stream=True,
                        proxies=proxies)

    # 构造响应
    resp = Response(response.iter_content(chunk_size=1024),
                    content_type=response.headers['Content-Type'],
                    status=response.status_code)
    return resp


if __name__ == '__main__':
    app.run(debug=True, port=5000)
