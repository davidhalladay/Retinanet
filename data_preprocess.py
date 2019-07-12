'''Load image/labels/boxes from an annotation file.

The list file is like:

    img.jpg xmin ymin xmax ymax label xmin ymin xmax ymax label ...
'''
from __future__ import print_function

import os
import sys
import random
import cv2
from retinanet import RetinaNet
from torch.autograd import Variable
import torch
import torch.utils.data as data
import torchvision.transforms as transforms

from PIL import Image, ImageDraw
import matplotlib.pyplot as plt
from encoder import DataEncoder
from transform import resize, random_flip, random_crop, center_crop

from pycocotools.coco import COCO
from class_cgf import *

def change_box_order(boxes, order):
    '''Change box order between (xmin,ymin,xmax,ymax) and (xcenter,ycenter,width,height).

    Args:
      boxes: (tensor) bounding boxes, sized [4].
      order: (str) either 'xyxy2xywh' or 'xywh2xyxy'.

    Returns:
      (tensor) converted bounding boxes, sized [4].
    '''
    assert order in ['xyxy2xywh','xywh2xyxy']
    if order == 'xywh2xyxy':
        x = boxes[0] ; y = boxes[1] ; w = boxes[2] ; h = boxes[3]
        return [x,y,x+w,y+h] #[x-w/2.,y-h/2.,x+w/2.,y+h/2.]
    if order == 'xyxy2xywh':
        xm = boxes[0] ; ym = boxes[1] ; xM = boxes[2] ; yM = boxes[3]
        w = xM - xm
        h = yM - ym
        return [xm+w/2.,ym+h/2.,w,h]

def load_data(root, ann_root,dataType):
    '''
    Args:
      root: (str) ditectory to images.
    '''
    fnames = os.listdir(root)
    fnames.sort()
    coco = COCO(ann_root)
    print("Total number of images : ",len(fnames))

    # save csv
    file = open("./data/%s.txt"%(dataType),"w")

    for i, name in enumerate(fnames):
        if (i+1)%10000 == 0:
            print("\r%d/%d"%(i+1,len(fnames)),end="")
        file.write("%s "%(name))
        img_num = int(name.replace(".jpg",""))
        annIds = coco.getAnnIds(imgIds=[img_num], iscrowd=None)
        anns = coco.loadAnns(annIds)
        for i, ann in enumerate(anns):
            coco_label = int(ann['category_id'])
            label = class_map(coco_label)
            # note that the order of BBox in COCO dataset is xywh where x and y is the up-left point
            # Not the center of BBox
            xywh = [float(ann['bbox'][0]),float(ann['bbox'][1]),float(ann['bbox'][2]),float(ann['bbox'][3])]
            bbox = change_box_order(xywh,'xywh2xyxy')

            file.write("%f %f %f %f %d "%(bbox[0],bbox[1],bbox[2],bbox[3],label))
        file.write("\n")
    return True

def test():
    import torchvision

    dataType = 'train2017'
    root = "../COCO_dataset/images/%s"%(dataType)
    ann_root = "../COCO_dataset/annotations/instances_%s.json"%(dataType)
    #load_data(root, ann_root,dataType)

    fnames = []
    boxes = []
    labels = []

    with open("./data/%s.txt"%(dataType)) as f:
        lines = f.readlines()

    for line in lines:
        splited = line.strip().split()
        fnames.append(splited[0])
        num_boxes = (len(splited) - 1) // 5
        box = []
        label = []
        for i in range(num_boxes):
            xmin = splited[1+5*i]
            ymin = splited[2+5*i]
            xmax = splited[3+5*i]
            ymax = splited[4+5*i]
            c = splited[5+5*i]
            box.append([float(xmin),float(ymin),float(xmax),float(ymax)])
            label.append(int(c))
        boxes.append(torch.Tensor(box))
        labels.append(torch.LongTensor(label))
    print("Total number of BBox : ",len(boxes))
    print("Total number of labels : ",len(labels))

    test_idx = 1000
    test_fname = fnames[test_idx]
    test_box = boxes[test_idx]
    test_label = labels[test_idx]

    img = Image.open(os.path.join(root,test_fname))

    draw = ImageDraw.Draw(img)
    for i,(box,label) in enumerate(zip(test_box,test_label)):
        draw.rectangle(list(box), outline=color_map(int(label)),width = 2)
        draw.rectangle(list([box[0],box[1]-10,box[0]+6*len(my_cate[int(label)])+4,box[1]]), outline=color_map(int(label)),width = 2,fill='white')
        draw.text((box[0]+3, box[1]-11), my_cate[int(label)],fill = (0, 0, 0, 100),width = 2)
    plt.imshow(img)
    plt.savefig("./test.jpg")



if __name__ == "__main__":
    test()
