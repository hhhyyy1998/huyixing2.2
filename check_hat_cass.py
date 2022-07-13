import os.path
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from draw_bbox import *
from requestModule import *
import uuid
import cv2

class Check_hat:
    def __init__(self):
        self.cate_regtime = {'hat': 0, 'uniform': 0}
        self.err_count = {'hat': 0, 'uniform': 0}
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
            #加密芯片
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
        draw_boxes(zip(labels, confidents, bboxs), image,
                   {'person': (0, 255, 0), 'head': (0, 0, 255)})
        head_bboxs = []
        person_bboxs = []
        cloth_bboxs = []

        red = (0, 0, 255)
        # 只记录最高置信度的cloth
        max_hat_confident = -1
        for label, confidence, bbox in zip(labels, confidents, bboxs):
            x, y, w, h = bbox
            left = max(0, int(round(x - (w / 2))))
            right = max(0, int(round(x + (w / 2))))
            top = max(0, int(round(y - (h / 2))))
            bot = max(0, int(round(y + (h / 2))))
            if label == 'head':
                head_bboxs.append((left, top, right, bot))
            if label == 'cloth':
                #记录下每一个衣服框的置信度
                if confidence>max_hat_confident:
                    max_hat_confident = confidence
                    cloth_bboxs=[(left, top, right, bot)]
            if label == 'person':
                person_bboxs.append((left, top, right, bot))

        no_hat = False
        no_uniform = False
        # 检测到人的情况下才做工作服，安全帽检测
        for person_bbox in person_bboxs:
            person_left, person_top, person_right, person_bottom = person_bbox
            person_mid = (person_left + person_right) // 2

            # 对于每一个头，找到与之对应的人
            for head_bbox in head_bboxs:
                head_left, head_top, head_right, head_bottom = head_bbox
                head_lfmid = (head_left + head_right) // 2
                if person_left <= head_lfmid <= person_right:
                    no_hat = True
                    cv2.putText(image, 'no hat',
                                (person_left, person_top + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, red, 2)

            # 置信度最高的cloth只要有person与之对应，就会判断未穿工作服
            for cloth_bbox in cloth_bboxs:
                cloth_left, cloth_top, cloth_right, cloth_bottom = cloth_bbox
                if cloth_left <= person_mid <= cloth_right:
                    no_uniform = True
                    cv2.putText(image, 'no uniform',
                                (person_left, person_top + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, red, 2)
                    draw_bbx(cloth_bbox,(0,0,255),image,'cloth')
        if no_hat:
            if self.err_count['hat'] >= 5:
                self.threadPool.submit(self.sendRequest, image, cate2code['hat'], TaskId, cate2desc['hat'], gap,
                                       alarm_pushUrl, dev_code, 'hat')
                self.err_count['hat'] = 0
            else:
                self.err_count['hat'] += 1
        else:
            if self.err_count['hat'] > 0:
                self.err_count['hat'] -= 1

        if no_uniform:
            if self.err_count['uniform'] >= 30:
                self.threadPool.submit(self.sendRequest, image, cate2code['uniform'], TaskId, cate2desc['uniform'], gap,
                                       alarm_pushUrl, dev_code, 'uniform')
                self.err_count['uniform'] = 0
            else:
                self.err_count['uniform'] += 1
        else:
            if self.err_count['uniform'] > 0:
                self.err_count['uniform'] -= 2
