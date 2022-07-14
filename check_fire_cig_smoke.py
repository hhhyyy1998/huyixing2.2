import os.path
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from draw_bbox import *
from requestModule import *
import uuid
import cv2

class Check_fire:
    def __init__(self):
        self.cate_regtime = {'smoke': 0, 'fire': 0, 'cigarette': 0}
        self.err_count = {'smoke': 0, 'fire': 0, 'cigarette': 0}
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

    '''
    image:cv2 image
    bboxs:list of bbox
    labels:list of label
    confidents:list of confident
    save_dir:save dir
    '''
    def check(self, image, bboxs, labels, confidents, save_dir, AlgCode, TaskId, cate2desc, gap, alarm_pushUrl,
              dev_code, cate2code):
        draw_boxes(zip(labels, confidents, bboxs), image,
                   {'fire': (0, 0, 255), 'smoke': (0, 0, 255), 'tabacco': (0, 0, 255),'hand':(0,255,0)})
        if 'fire' in labels:
            if self.err_count['fire'] >= 3:
                cv2.putText(image, 'fire!', (100, 100), cv2.FONT_ITALIC, 1, (255, 0, 0), 2)
                # save_info(save_dir,'smoke_fire',image,self.cate_regtime,gap=gap)
                self.threadPool.submit(self.sendRequest, image, cate2code['fire'], TaskId, cate2desc['fire'], gap,
                                       alarm_pushUrl, dev_code, 'fire')
                self.err_count['fire'] = 0
            else:
                self.err_count['fire'] += 1
        else:
            self.err_count['fire'] = self.err_count['fire'] - 1 if self.err_count['fire'] - 1 >= 0 else 0
        if 'smoke' in labels:
            if self.err_count['smoke'] >= 3:
                cv2.putText(image, 'smoke!', (100, 200), cv2.FONT_ITALIC, 1, (255, 0, 0), 2)
                # save_info(save_dir,'smoke_fire',image,self.cate_regtime,gap=gap)
                self.threadPool.submit(self.sendRequest, image, cate2code['smoke'], TaskId, cate2desc['smoke'], gap,
                                       alarm_pushUrl, dev_code, 'smoke')
                self.err_count['smoke'] = 0
            else:
                self.err_count['smoke'] += 1
        else:
            self.err_count['smoke'] = self.err_count['smoke'] - 1 if self.err_count['smoke'] - 1 >= 0 else 0

        if 'tabacco' in labels and 'hand' in labels:
            tabacco_bbox = []
            hand_bbox = []
            for label, confidence, bbox in zip(labels, confidents, bboxs):
                x, y, w, h = bbox
                left = max(0, int(round(x - (w / 2))))
                right = max(0, int(round(x + (w / 2))))
                top = max(0, int(round(y - (h / 2))))
                bot = max(0, int(round(y + (h / 2))))
                if label == 'tabacco':
                    tabacco_bbox.append((left, top, right, bot))
                if label == 'hand':
                    hand_bbox.append((left, top, right, bot))
            #遍历所有香烟，寻找是否在手上
            for tbox in tabacco_bbox:
                tb_left, tb_top, tb_right, tb_bottom = tbox
                cig_in_hand = False
                for hbox in hand_bbox:
                    # 判断香烟是否在手上
                    hd_left, hd_top, hd_right, hd_bottom = hbox
                    if ((tb_left >= hd_left and tb_left <= tb_right) or (
                            tb_right >= tb_left and hd_right <= hd_right) or (
                            tb_top >= hd_top and tb_top <= hd_bottom) or (
                            tb_bottom >= hd_top and tb_bottom <= hd_bottom)):
                        cig_in_hand = True
                        break
            if cig_in_hand:
                if self.err_count['cigarette'] >= 5:
                    cv2.putText(image, 'cigarette!', (100, 300), cv2.FONT_ITALIC, 1, (255, 0, 0), 2)
                    self.threadPool.submit(self.sendRequest, image, cate2code['cigarette'], TaskId, cate2desc['cigarette'],
                                           gap, alarm_pushUrl, dev_code, 'cigarette')
                    self.err_count['cigarette'] = 0
                else:
                    self.err_count['cigarette']+=1
            else:
                if self.err_count['cigarette'] > 0:
                    self.err_count['cigarette'] -= 2
