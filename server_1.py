from flask import Flask, request, jsonify
from gevent import pywsgi
import os
# 创建一个服务
app = Flask(__name__)
import uuid
import os
import base64
import json

import numpy as np
# 创建一个接口 指定路由和请求方法 定义处理请求的函数
if not os.path.exists('./save'):
    os.makedirs('./save')
@app.route(rule='/analysis/alarm_push/', methods=['POST'])
def everything():
    save_info_file = f'./save/{uuid.uuid4().hex}.txt'
    if request.files:
        request.files['image'].save(os.path.join('./save',request.files['image'].filename))
    else:
        rdata = json.loads(request.data.decode('utf-8'))
        print(rdata)

    return request.data
if __name__ == '__main__':
    server = pywsgi.WSGIServer(('192.168.1.4', 8807), app)
    print('server is running...')
    server.serve_forever()

