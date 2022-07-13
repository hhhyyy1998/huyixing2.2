import cv2
import random

def class_colors(names):
    """
    Create a dict with one random BGR color for each
    class name
    """
    return {name: (
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255)) for name in names}


def bbox2points(bbox):
    """
    From bounding box yolo format
    to corner points cv2 rectangle
    """
    x, y, w, h = bbox
    xmin = int(round(x - (w / 2)))
    xmax = int(round(x + (w / 2)))
    ymin = int(round(y - (h / 2)))
    ymax = int(round(y + (h / 2)))
    return xmin, ymin, xmax, ymax

def draw_bbx(bbox,color,image,label):
    left, top, right, bottom = bbox2points(bbox)
    cv2.rectangle(image, (left, top), (right, bottom), color, 1)
    cv2.putText(image, label,
                (left, top +5), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                color, 2)
def draw_boxes(detections, image, colors):
    for label, confidence, bbox in detections:
        if label not in colors.keys():
            continue
        left, top, right, bottom = bbox2points(bbox)
        cv2.rectangle(image, (left, top), (right, bottom), colors[label], 1)
        cv2.putText(image, "{} [{:.2f}]".format(label, float(confidence)),
                    (left, top - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    colors[label], 2)
    return image