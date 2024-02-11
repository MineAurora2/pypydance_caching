# 安装依赖命令
# pip install -i https://pypi.tuna.tsinghua.edu.cn/simple OpenSSL
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

@app.route('/api/v1/videos/<video_id>.mp4')
def get_video(video_id):
    print("加载视频:" + str(video_id))

    # 检查视频是否已经被缓存
    video_path = os.path.join(VIDEO_CACHE_DIR, f'{video_id}.mp4')
    if not os.path.exists(video_path):
        print("本视频没有缓存，正在从视频站拉取...")
        # 如果没有缓存，则下载视频
        video_url = f'http://jd.pypy.moe/api/v1/videos/{video_id}.mp4'
        response = requests.get(video_url, proxies=proxies)
        # response = requests.get(video_url,proxies=None)
        if response.status_code == 200:
            # 保存视频到缓存目录
            with open(video_path, 'wb') as video_file:
                video_file.write(response.content)
            print("视频下载成功")
        else:
            return "视频下载失败", 500

    # 从缓存目录返回视频
    print("视频从缓存中加载成功")
    return send_file(video_path)


@app.route('/<path:path>')
def proxy(path):
    print("加载其他url: " + str(path))
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
    response = req_func(original_url, headers=headers, data=request.data, params=request.args, stream=True, proxies=proxies)

    # 构造响应
    resp = Response(response.iter_content(chunk_size=1024),
                    content_type=response.headers['Content-Type'],
                    status=response.status_code)
    return resp

if __name__ == '__main__':
    app.run(debug=True, port=5000)


