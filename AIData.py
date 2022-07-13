import json
import os
def ability_res(number, ai_ability):
    data = {
        "EventType": "alg_ability_request",
        "Result":
            {
                "Code": 200,
                "Desc": "算法能力查询成功"
            },
        "AbilityInfo":
            {
                "Number": number,
                "Ability": ai_ability

            }
    }

    return data

def task_config_res(task_id):
    data = {
        "EventType": "alg_task_config",
        "TaskId": task_id,
        "Result": {
            "Code": 200,
            "Desc": "success"
        }
    }
    return data


def config_fail_res(task_id,Desc='fail'):
    data = {
        "EventType": "alg_task_config",
        "TaskId": task_id,
        "Result": {
            "Code": 400,
            "Desc": Desc
        }
    }
    return data


def task_request_res(task_number, task,Desc='success'):
    data = {
        "EventType": "alg_task_request",
        "Result": {
            "Code": 200,
            "Desc": Desc
        },
        "TaskNumber": task_number,
        "Task": task
    }
    return data
