import cv2
import os.path
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from draw_bbox import *
from requestModule import *
import uuid

class Check_fence:
    def __init__(self):
        self.cate_regtime = {'fence': 0}
        self.err_count = {'fence': 0}
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
        draw_boxes(zip(labels, confidents, bboxs), image,{'person': (0, 255,0), 'fence': (255, 0, 0),'fence2':(255,0,0),'fence3':(255,0,0)})
        person_foot_lines = []
        fence_points = []
        fence_bboxs = []
        for label, confidence, bbox in zip(labels, confidents, bboxs):
            x, y, w, h = bbox
            left_top = (x - w / 2, y - h / 2)
            right_top = (x + w / 2, y - h / 2)
            right_bottom = (x + w / 2, y + h / 2)
            left_bottom = (x - w / 2, y + h / 2)
            if label == 'person':
                person_foot_lines.append((left_bottom, right_bottom))
            if label == 'fence' or label == 'fence2' or label == 'fence3':
                fence_points.append((left_top, right_top, right_bottom, left_bottom))
                fence_bboxs.append(bbox)
        # fence detection

        if_fence = False

        if person_foot_lines and fence_points:
            for foot_line in person_foot_lines:
                left_bot = foot_line[0]
                right_bot = foot_line[1]
                for i,fs in enumerate(fence_points):
                    lt, rt, rb, lb = fs[0], fs[1], fs[2], fs[3]
                    if left_bot[0] >= lt[0] and right_bot[0] <= rt[0] and left_bot[1] <= lb[1] and left_bot[1] >= lt[1]:
                        if_fence = True
                        draw_bbx(fence_bboxs[i],(0,0,255),image,'Enter the guardrail')
                        cv2.putText(image, 'Enter the guardrail', (100, 300), cv2.FONT_ITALIC, 1, (255, 0, 0), 2)

        #如果发生了闯入行为
        if if_fence:
            #判断是否在发生了多次,如果是，就发送警报
            if self.err_count['fence']>=10:
                self.threadPool.submit(self.sendRequest, image, cate2code['fence'], TaskId, cate2desc['fence'], gap,
                                       alarm_pushUrl, dev_code, 'fence')
            else:
                self.err_count['fence'] +=1
        else:
            if self.err_count['fence']>0:
                self.err_count['fence']-=2