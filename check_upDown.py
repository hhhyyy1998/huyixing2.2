import cv2
import os.path
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from draw_bbox import *
from requestModule import *
import uuid

class Check_upDown:
    def __init__(self):
        self.cate_regtime = {'upDown': 0}
        self.err_count = {'upDown': 0}
        self.threadPool = ThreadPoolExecutor(max_workers=5)
        self.lock = threading.RLock()
        with open('algCode.json', 'r') as f:
            configs = json.load(f)
            self.inter_ip_text = configs['inter_ip_text']
            self.inter_ip_img = configs['inter_ip_img']
            self.ifcloud = configs['ifcloud']

    def sendRequest(self,image,AlgCode,TaskId,Desc,gap,alarm_pushUrl,dev_code,cate):
        self.lock.acquire()
        curtime = self.cate_regtime[cate]
        if time.time() - curtime >= gap:
            pictureName = f'{TaskId}_{AlgCode}_{uuid.uuid4().hex}.jpg'
            tempPath = './temp/'
            if not os.path.exists(tempPath):
                os.makedirs(tempPath)
            picPath = os.path.join(tempPath, pictureName)
            cv2.imwrite(picPath, image)
            infos = [
                {
                    "AlgCode": AlgCode,
                    "TaskId": TaskId,
                    "AlarmTime": time.strftime('%Y-%m-%d %H:%M:%S'),
                    "Desc": Desc,
                    "PictureName": pictureName,
                    "Type": 0,
                    "Width": image.shape[1],
                    "Height": image.shape[0],
                    "Size": os.stat(picPath).st_size,
                }
            ]

            # 加密芯片
            push_info_chip(alarm_pushUrl, infos)
            push_img_chip(alarm_pushUrl, pictureName, picPath)

            #云平台
            if self.ifcloud:
                push_info_cloud(self.inter_ip_text, infos, dev_code)
                push_img_cloud(self.inter_ip_img,pictureName,picPath,dev_code)
            os.remove(picPath)
            self.cate_regtime[cate] = time.time()
            self.lock.release()

    def check(self, image, bboxs, labels, confidents, save_dir,AlgCode,TaskId,cate2desc,gap,alarm_pushUrl,dev_code,cate2code):
        draw_boxes(zip(labels, confidents, bboxs), image,{'Up': (255, 0,0), 'Down': (0, 0, 255),'Squat':(255,0,0)})
        
        #如果发生了闯入行为
        if 'Down' in labels:
            print( self.err_count['upDown'])
            #判断是否在发生了多次,如果是，就发送警报
            if self.err_count['upDown']>=5:
                self.threadPool.submit(self.sendRequest, image, cate2code['upDown'], TaskId, cate2desc['upDown'], gap,
                                       alarm_pushUrl, dev_code, 'upDown')
            else:
                self.err_count['upDown'] += 1
        else:
            if self.err_count['upDown']>0:
                self.err_count['upDown']-=2