import json
import os
import socket
import subprocess
import threading
import time
import copy
from flask import Flask, request, make_response
from gevent import pywsgi

from AIData import ability_res, task_config_res, config_fail_res, task_request_res

# 创建一个服务
app = Flask(__name__)

# 加载算法列表
with open('algCode.json', 'rb') as f:
    configs = json.load(f)
ability = configs['code2desc']
code_list=[]
code2desc = {}
for abi in ability:
    code2desc[abi['AlgCode']] = abi['CodeDesc']
    code_list.append(abi['AlgCode'])
# 加载运行算法对应的Py文件
cde2pyfiles = configs['code2pyfile']
cde2pyfile = {}
for c2p in cde2pyfiles:
    for code in c2p['AlgCode']:
        cde2pyfile[code] = c2p['pyfile']
Ipc_code = configs['Ipc_code']

# 用于记录当前任务状态
tasks = {}
# 用户记录当前算法的开启状态
alg_stat = {}
alg_codes = [alb['AlgCode'] for alb in ability]  # 算法编号

# 开启服务的ip
ipv4 = configs['IPV4']

# 布控球ip
camera_ip = configs['IPV4']


# 守护线程，用于检查任务的状态，如果是异常关闭,将把任务状态设置为-2(异常关闭)
def check_task():
    global tasks
    while True:
        time.sleep(1)
        for tid in tasks:
            proc = tasks[tid]['proc']
            stat = tasks[tid]['state']
            acode = tasks[tid]['AlgCode']
            if proc.poll() is not None:
                if stat == 1:
                    print('发现程序异常中断')
                    tasks[tid]['state'] = -2
                    alg_stat[cde2pyfile[acode]] = False

check_task_daemon = threading.Thread(target=check_task)
check_task_daemon.daemon = True
check_task_daemon.start()

m=1
@app.route(rule='/analysis/interface/', methods=['POST'])
def everything():
    global tasks
    global alg_stat
    global request_data
    # 1.获取 JSON 格式的请求体 并解析拿到数据
    if m==0:
        request_data = json.loads(request.data.decode('utf-8'))
    print('request data:', request_data)
    event_type = request_data['EventType']  # 事件类型

    # 2.1 设备算法能力查询
    if event_type == 'alg_ability_request':
        try:
            # 获取能力列表的数量和内容，并返回
            number = len(ability)
            temp_abi = copy.deepcopy(ability)
            for alb in temp_abi:
                alb['AlgCode'] = int(alb['AlgCode'])
            response_data = ability_res(number, temp_abi)
        except Exception:
            # 查询失败
            inquire_fail_data = {
                "EventType": "alg_ability_request",
                "Result":
                    {
                        "Code": 400,
                        "Desc": "查询算法能力失败"
                    }
            }
            # 生成响应信息
            response_data = inquire_fail_data
        response = make_response(response_data)
        response.headers['Content-Type'] = 'application/json'
        return response
    # 2.2 算法任务配置
    elif event_type == 'alg_task_config':
        # 算法任务配置
        # 配置结果 -> task_config_res
        # 停止\删除分析任务时,只需填写EventType,TaskId和Command四个字段
        try:
            command = str(request_data['Command'])  # 字符串,配置配命令,0停止 1开始 2删除
            task_id = request_data['TaskId']  # 字符串,分析任务ID

            if command not in('0','1','2'):
                response_data = config_fail_res(task_id, '开启失败,配置命令不存在')
                response = make_response(response_data)
                response.headers['Content-Type'] = 'application/json'
                return response
            alg_code = request_data['AlgCode']  # 字符串,算法能力编码
            print('command:',command)
            # 启动任务
            if command == '1':
                if alg_code not in alg_codes:
                    response_data = config_fail_res(task_id, '开启失败,算法能力代码不存在')
                    response = make_response(response_data)
                    response.headers['Content-Type'] = 'application/json'
                    return response
                dev_code = request_data['DevCode']  # 字符串,设备唯一编码
                alarm_interval = request_data['AlarmInterval']  # 整形,告警间隔,单位秒
                alarm_pushUrl = request_data['AlarmPushUrl']  # 字符串,告警推送地址
                desc = code2desc[alg_code]

                if task_id in tasks and tasks[task_id]['state'] == 1:
                    response_data = config_fail_res(task_id, '开启失败,该id任务已开启')
                    response = make_response(response_data)
                    response.headers['Content-Type'] = 'application/json'
                    return response

                if alg_stat.get(cde2pyfile[alg_code], False) == True:
                    response_data = config_fail_res(task_id, '开启失败,算法已开启')
                    response = make_response(response_data)
                    response.headers['Content-Type'] = 'application/json'
                    return response

                
                

                # 需要执行的python文件
                exfile = cde2pyfile[alg_code]
                print(exfile)
                print(
                    f'python {exfile} --dev_code {dev_code} --AlgCode {alg_code} --TaskId {task_id} --gap {alarm_interval} --Desc {desc} --alarm_pushUrl {alarm_pushUrl}')
                proc = subprocess.Popen(
                    [
                        f'python {exfile} --dev_code {dev_code} --AlgCode {alg_code} --TaskId {task_id} --gap {alarm_interval} --Desc {desc} --alarm_pushUrl {alarm_pushUrl}'],
                    shell=True,executable='bash')
                tasks[task_id] = {}
                tasks[task_id]['proc'] = proc
                tasks[task_id]['AlgCode'] = alg_code
                tasks[task_id]['alarm_interval'] = alarm_interval
                tasks[task_id]['alarm_pushUrl'] = alarm_pushUrl
            
                if not proc.poll():
                    print('success')
                    tasks[task_id]['state'] = 1
                    alg_stat[cde2pyfile[alg_code]] = True
                    print("tasks:",tasks)
                    print(request_data['DevCode'])
                    print(alg_stat)
                    if m==0:
                        file=open('/home/firefly/huyixing2.2/tasks.txt','a')
                        file.write(alg_code+'\n'+str(alarm_interval)+'\n'+alarm_pushUrl+'\n'+request_data['DevCode']+'\n\n')
                        file.close()
                else:
                    tasks[task_id]['state'] = -1
            # 停止任务
            if command == '0':
                if task_id not in tasks:
                    response_data = config_fail_res(task_id, '停止失败,任务id不存在')
                    response = make_response(response_data)
                    response.headers['Content-Type'] = 'application/json'
                    return response
                elif tasks[task_id]['state'] != 1:
                    response_data = config_fail_res(task_id, '停止失败,任务未开启')
                    response = make_response(response_data)
                    response.headers['Content-Type'] = 'application/json'
                    return response
                os.kill(tasks[task_id]['proc'].pid, 9)
                tasks[task_id]['state'] = 0
                alg_stat[cde2pyfile[alg_code]] = False
                n=0
                with open('tasks.txt','r') as f:
                     lines=f.readlines()
                     with open('tasks.txt','w') as f_w:
                            for line in lines:
                                  if alg_code==line[0:-1]:
                                         print('alg_code:',alg_code)
                                         del lines[n:n+4]
                                         continue
                                  n+=1
                                  f_w.write(line)
            print("task_id:",task_id)
            response_data = task_config_res(task_id)
            # 删除任务
            if command == '2':
                if task_id not in tasks:
                    response_data = config_fail_res(task_id, '删除失败,任务id不存在')
                    response = make_response(response_data)
                    response.headers['Content-Type'] = 'application/json'
                    return response
                if tasks[task_id]['state'] == 1:
                    response_data = config_fail_res(task_id, '删除失败,任务正在运行,请先停止后删除!')
                    response = make_response(response_data)
                    response.headers['Content-Type'] = 'application/json'
                    return response
                tasks.pop(task_id)

        except KeyError:
            response_data = config_fail_res(task_id, '参数错误/不全')
        except Exception as e:
            # 配置失败
            response_data = config_fail_res(task_id, '未知错误')

            print(repr(e))
        if m==0:
            print("response_data:",response_data)
            response = make_response(response_data)
            print("response:",response)
            response.headers['Content-Type'] = 'application/json'
            return response
    # 2.3 算法任务配置
    elif event_type == 'alg_task_request':
        # 分析任务状态, 任务异常停止(-2), 任务创建失败(-1), 任务空闲(0), 任务正在运行(1), 任务正在创建(2)
        # 查询结果 -> GlobalResult.task_request_res
        try:
            task_number = len(tasks)
            task = []
            for taskid in tasks.keys():
                temp = {
                    'TaskId': taskid,
                    'AlgCode': tasks[taskid]['AlgCode'],
                    'TaskStatus': tasks[taskid]['state']
                }
                task.append(temp)
            # 查询成功
            response_data = task_request_res(task_number, task)
        except:
            # 查询失败
            request_fail_data = {
                "EventType": "alg_ability_request",
                "Result":
                    {
                        "Code": 400,
                        "Desc": "fail"
                    }
            }
            response_data = request_fail_data
        response = make_response(response_data)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response_data = {"Message": "请求失败,事件类型错误"}
        response = make_response(response_data)
        response.headers['Content-Type'] = 'application/json'
        return response

if os.path.exists('tasks.txt')==True:
    with open('tasks.txt','r') as f:
        lines=f.readlines()
        p=0
        for line in lines:
            if line[0:-1] in code_list:
                  a=line[0:-1]
                  b=lines[p+1][0:-1]
                  c=lines[p+2][0:-1]
                  d=lines[p+3][0:-1]
                  request_data={'EventType': 'alg_task_config', 'TaskId': a, 'DevCode': d, 'Command': 1, 'AlgCode': a, 'AlarmInterval': b, 'AlarmPushUrl': c}
                  everything()
            p+=1     
m=0

@app.route(rule='/2500/ipc/get/', methods=['POST'])
def everything_get_id():
    response = make_response({"Ipc_code": Ipc_code})
    response.headers['Content-Type'] = 'application/json'
    return response


def get_host_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip


if __name__ == '__main__':
    # 启动服务 指定主机和端口
    hostip = ipv4 if ipv4 != "" else get_host_ip()
    server = pywsgi.WSGIServer((hostip, 3002), app)
    print('server is running at ' + hostip)
    server.serve_forever()
