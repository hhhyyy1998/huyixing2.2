import requests
import json


# 获取设备id
def get_dev_id():
    dev_url = 'http://127.0.0.1:8807/2500/ipc/get/'
    # 头部信息
    headers = {
        'Content-Type': 'application/json'
    }
    data = {
        "EventType": "get_device_id"
    }
    r = requests.post(dev_url, data=json.dumps(data), headers=headers)
    if r.status_code == 200:
        print('设备ID获取成功！')
        DeviceSno = r.text
    else:
        print('设备ID获取失败！')
        DeviceSno = '{"DeviceSno": ''}'

    print(DeviceSno)
    return DeviceSno

# 告警图片推送
# 1.云平台推送图片
def push_img_cloud(url, alarm_img_name, alarm_img_url,dev_code):
    # 地址1:云平台地址
    # url_1 = "https://surveillance-api.whhyxkj.com/camera/api/violation-manage/upload/file"
    with open(alarm_img_url,'rb') as f:
        files = [
            ('image', (alarm_img_name, f, 'image/jpeg'))
        ]
        headers = {
            "token": 'eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJzeXN0ZW0iLCJuYW1lIjoi6L-d56ug5LiK5LygIiwidHlwZSI6IjEiLCJ1c2VySWQiOiJzeXN0ZW0iLCJpYXQiOjE2NDgwMTg4NzJ9.HilTvzEUBul2JGJq2NlbxA2OUCgglauhYHFGv6KcPnHSnCPYJK5xgSNnLoFi67W5TkBOBDgf3X_r2h0fS-eihw'
        }
        # 平台1图片推送
        r_1 = requests.request("POST", url, headers=headers, files=files)
        if r_1.status_code == 200:
            print('云平台图片推送成功', r_1.status_code)
            print(r_1.text)
        else:
            print('云平台图片推送失败', r_1.status_code)
            print(r_1.text)

# 2.加密芯片推送图片
def push_img_chip(url, alarm_img_name, alarm_img_url):
    with open(alarm_img_url,'rb') as f:
        files = [
            ('image', (alarm_img_name, f, 'image/jpeg'))
        ]
        headers = {
            "token": 'eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJzeXN0ZW0iLCJuYW1lIjoi6L-d56ug5LiK5LygIiwidHlwZSI6IjEiLCJ1c2VySWQiOiJzeXN0ZW0iLCJpYXQiOjE2NDgwMTg4NzJ9.HilTvzEUBul2JGJq2NlbxA2OUCgglauhYHFGv6KcPnHSnCPYJK5xgSNnLoFi67W5TkBOBDgf3X_r2h0fS-eihw'
        }
        r_2 = requests.request("POST", url, headers=headers, files=files)
        if r_2.status_code == 200:
            print(r_2.text)
            print('加密芯片图片推送成功', r_2.status_code)
            print(r_2.text)
        else:
            print('加密芯片图片推送失败', r_2.status_code)
            print(r_2.text)

        return r_2.status_code


# 告警信息推送

# 3.云平台推送告警信息
def push_info_cloud(url, alarm_info,dev_code):
    # 地址1：云平台
    # url_1 = "https://surveillance-api.whhyxkj.com/camera/api/violation-manage/upload/violation"

    # 头部信息
    headers = {
        "Content-Type": 'application/json',
        "token": 'eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJzeXN0ZW0iLCJuYW1lIjoi6L-d56ug5LiK5LygIiwidHlwZSI6IjEiLCJ1c2VySWQiOiJzeXN0ZW0iLCJpYXQiOjE2NDgwMTg4NzJ9.HilTvzEUBul2JGJq2NlbxA2OUCgglauhYHFGv6KcPnHSnCPYJK5xgSNnLoFi67W5TkBOBDgf3X_r2h0fS-eihw'
    }
    data_2 = {
        "EventType":
            "alg_task_alarm_push",
        "AlarmInfo":
            {
                "Number": 1,
                "Item": alarm_info
            }
    }

    # 云平台推送,加推送设备ID
    # 得到设备ID
    # device_id = json.loads(get_dev_id())['DeviceSno']
    data_2['AlarmInfo']['Item'][0]['DeviceSno'] = dev_code
    r_1 = requests.post(url, data=json.dumps(data_2), headers=headers)

    if r_1.status_code == 200:
        print('云平台告警信息推送成功', r_1.status_code)
        print(r_1.text)
    else:
        print('云平台告警信息推送失败', r_1.status_code)


# 4.加密芯片推送告警信息
def push_info_chip(url, alarm_info):
    # 头部信息
    headers = {
        "Content-Type": 'application/json',
        "token": 'eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJzeXN0ZW0iLCJuYW1lIjoi6L-d56ug5LiK5LygIiwidHlwZSI6IjEiLCJ1c2VySWQiOiJzeXN0ZW0iLCJpYXQiOjE2NDgwMTg4NzJ9.HilTvzEUBul2JGJq2NlbxA2OUCgglauhYHFGv6KcPnHSnCPYJK5xgSNnLoFi67W5TkBOBDgf3X_r2h0fS-eihw'
    }
    data = {
        "EventType":
            "alg_task_alarm_push",
        "AlarmInfo":
            {
                "Number": 1,
                "Item": alarm_info
            }
    }
    # 信息推送
    r_2 = requests.request("POST", url, data=json.dumps(data), headers=headers)


    if r_2.status_code == 200:
        print('加密芯片告警信息推送成功', r_2.status_code)
        print(r_2.text)
    else:
        print('加密芯片告警信息推送失败', r_2.status_code)
        print(r_2.text)


if __name__ == '__main__':
    test_test = [
        {
            "AlgCode": 1001,
            "TaskId": "AlgTask123",
            "AlarmTime": "2022-03-24 12:03:00",
            "Desc": "作业现场吸烟",
            "PictureName": "281230.jpg",
            "Type": 0,
            "Width": 1080,
            "Height": 720,
            "Size": 180309,
        }
    ]


    # 测试 加密平台
    # push_info_chip('http://127.0.0.1:8807/analysis/alarm_push/', test_test)
    push_img_chip('http://127.0.0.1:8807/analysis/alarm_push/', 'img0.jpg','./img0.jpg')
    #
    # # 测试 云平台
    # push_info_cloud('https://surveillance-api.whhyxkj.com/camera/api/violation-manage/upload/violation', test_test)
    # push_img_cloud('https://surveillance-api.whhyxkj.com/camera/api/violation-manage/upload/file', '281230.jpg',
    #                './281230.jpg')

