import time
import os
import cv2
'''
save_dir:保存信息的主文件夹
cate:类别，决定保存信息的文件夹
image:图片
cate_regtime:上一次保存的时间，每间隔gap时间才会保存同类信息
gap：保存间隔时间
words:保存的信息，默认不填写的话就是cate
'''
def save_info(save_dir, cate, image, cate_regtime,gap=5,words = None):
    curtime = time.time()
    if curtime - cate_regtime[cate] >= gap:
        cate_regtime[cate] = curtime
        day = time.strftime('%Y_%m_%d')
        dir = f'{save_dir}/{day}/{cate}'
        if not os.path.exists(dir):
            os.makedirs(dir, )
        file_name = f'{cate}.txt'
        file_path = os.path.join(dir, file_name)
        if words:
            info = f'{time.asctime()} {words}\n'
        else:
            info = f'{time.asctime()} {cate}\n'
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                f.write(info)
        else:
            with open(file_path, 'a') as f:
                f.write(info)
        img_dir = f'{save_dir}/{day}/{cate}/imgs'
        if not os.path.exists(img_dir):
            os.makedirs(img_dir)
        image_name = f'{time.asctime()} {cate}.jpg'
        img_path = os.path.join(img_dir, image_name)
        cv2.imwrite(img_path, image)