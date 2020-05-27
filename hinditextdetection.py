# -*- coding: utf-8 -*-
"""HindiTextDetection.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1ROnJx4dKR99vonweybRnO0R1D4zqhtLK

Hindi Text Detection using Detectron 2
"""

!pip install -U torch==1.4+cu100 torchvision==0.5+cu100 -f https://download.pytorch.org/whl/torch_stable.html 
!pip install cython pyyaml==5.1
!pip install -U 'git+https://github.com/cocodataset/cocoapi.git#subdirectory=PythonAPI'
!pip install detectron2 -f https://dl.fbaipublicfiles.com/detectron2/wheels/cu100/index.html

#mount the google drive and then run this command
!unzip "/content/drive/My Drive/GUVI_Capstone/detectron2-master.zip"

#-----------------How to unzip 7z and tar files--------------------------
#!apt-get install p7zip-full
#!p7zip -d "/content/drive/My Drive/GUVI_Capstone/Synthetic Train Set (100k) - Detection & Recognition.tar.7z"
!tar -xf"/content/drive/My Drive/GUVI_Capstone/Synthetic Train Set - Detection & Recognition.tar"
#!p7zip -d "/content/drive/My Drive/GUVI_Capstone/Synthetic Train Set (100k) - Detection & Recognition.tar.7z"
#!tar -xf "/content/Synthetic Train Set - Detection & Recognition.tar"

#-------To delete a folder--------------------
#!rm -rf 'Foldername'

!wget https://github.com/bgshih/cocotext/releases/download/dl/cocotext.v2.zip

!unzip cocotext.v2.zip

import random
import os
import numpy as np
import json
import itertools
import cv2
import torch
import shutil
import math
from tqdm import tqdm

from detectron2.data import DatasetCatalog, MetadataCatalog
from detectron2.engine import DefaultTrainer, DefaultPredictor
from detectron2.config import get_cfg
from detectron2.utils.visualizer import Visualizer, ColorMode
from google.colab.patches import cv2_imshow
from detectron2.structures import BoxMode

print(torch.cuda.device(0))
print(torch.cuda.get_device_name(0))
cuda0 = torch.device('cuda:0')

#This cell will split the data into Train and Validation

#Calibration for Train and Val split ratio
TrainTestSplit = 0.01

#Creating Train Folder
os.mkdir('/content/Synthetic Train Set - Detection & Recognition/Train')

#Moving data from folder 'Synthetic Train Set - Detection & Recognition' to Train
path = "/content/Synthetic Train Set - Detection & Recognition/"
moveto = "/content/Synthetic Train Set - Detection & Recognition/Train/"
files = os.listdir(path)
files.sort()
for f in files:
    if f == 'Train':
      pass
    else: 
      src = path+f
      dst = moveto+f
      shutil.move(src,dst)

#Creating folder structure for Val, same as Train
TrainAnno = '/content/Synthetic Train Set - Detection & Recognition/Train/Annotation'
TrainImg  = '/content/Synthetic Train Set - Detection & Recognition/Train/Image'
ValAnno = '/content/Synthetic Train Set - Detection & Recognition/Val/Annotation'
ValImg = '/content/Synthetic Train Set - Detection & Recognition/Val/Image'

for x in os.listdir(TrainAnno):
  os.makedirs(ValAnno+'/'+x)
for y in os.listdir(TrainImg):
  os.makedirs(ValImg+'/'+y)

#Split Dataset (images and annotations) to Train and Val
random.seed(0)
for i in os.listdir(TrainAnno):
    for m in random.sample(os.listdir(TrainAnno+'/'+i),math.ceil(len(os.listdir(TrainAnno+'/'+i))*TrainTestSplit)):
        shutil.move(TrainAnno+'/'+i+'/'+m,ValAnno+'/'+i+'/'+m)
        m1 = m[:-4]
        m1 = m1+'.jpg'
        shutil.move(TrainImg+'/'+i+'/'+m1,ValImg+'/'+i+'/'+m1)

def get_dicts(img_dir):
  basepath = img_dir+'/Image'
  annopath = img_dir+'/Annotation'
  dataset_dicts = []
  for folder in tqdm(os.listdir(basepath)):
    basepath1 = basepath+'/'+folder
    annopath1 = annopath+'/'+folder
    for entry in os.listdir(basepath1):
        record = {}
        record["file_name"] = (basepath1+'/'+entry)
        height, width = cv2.imread(basepath1+'/'+entry).shape[:2]
        record["height"] = height
        record["width"] = width
        record["image_id"] = entry
        dataset_dicts.append(record)
        #--------------Annotation Related -------------------------
        entry1 = entry[:-4]
        entry1 = entry1+'.txt'
        my_file = open(annopath1+'/'+ entry1, "r")
        content = my_file.read()
        content_list = content.split("\n")
        for i in content_list:
            if i == "":
              content_list.remove(i)
        #print(annos)
        temp_dicts = []
        for x in content_list:
            w = {}
            w = x.split(" ")
            temp_dicts.append(w)
        #print(temp_dicts)

        bx = []
        by = []
        ba = []
        for i in temp_dicts:
            ax = i[:4]
            ax = [float(j) for j in ax]
            bx.append(ax)
            ay = i[4:8]
            ay = [float(k) for k in ay]
            by.append(ay)
            aa = i[8:9]
            ba.append(aa)
        # print(temp_dicts)# print(bx)# print(by)# print(ba)
        px = []
        py = []
        pa = []
        objs = []
        for annox,annoy,annoz in zip(bx,by,ba):
            px = annox
            py = annoy
            pa = annoz
            poly = [(x + 0.5, y + 0.5) for x, y in zip(px, py)]
            poly = list(itertools.chain.from_iterable(poly))
            # print(px)# print(py)# print(poly)# print(pa)
            obj = {
                    "bbox": [np.min(px), np.min(py), np.max(px), np.max(py)],
                    "bbox_mode": BoxMode.XYXY_ABS,
                    "segmentation": [poly],
                    "category_id": 0,
                    "iscrowd": 0
            }
            objs.append(obj)
        record["annotations"] = objs
        dataset_dicts.append(record)
        my_file.close()
    #print(len(dataset_dicts))
        
  return (dataset_dicts)

for d in ["Train", "Val"]:
    DatasetCatalog.register("basepath_"+d, lambda d=d: get_dicts("/content/Synthetic Train Set - Detection & Recognition/"+d))
    MetadataCatalog.get("basepath_"+d).set(thing_classes=["H"])
My_metadata = MetadataCatalog.get("basepath_Train")

dataset_dicts = get_dicts('/content/Synthetic Train Set - Detection & Recognition/Train')

for d in random.sample(dataset_dicts, 3):
    img = cv2.imread(d["file_name"])
    print(d["file_name"])
    visualizer = Visualizer(img[:, :, ::-1], metadata=My_metadata, scale=0.5)
    vis = visualizer.draw_dataset_dict(d)
    cv2_imshow(vis.get_image()[:, :, ::-1])

cfg = get_cfg()
cfg.merge_from_file("/content/detectron2-master/configs/COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_3x.yaml")
#cfg.merge_from_file("/content/detectron2-master/configs/COCO-InstanceSegmentation/mask_rcnn_R_101_FPN_3x.yaml")
cfg.DATASETS.TRAIN = ("basepath_Train",)
cfg.DATASETS.TEST = ()
cfg.DATALOADER.NUM_WORKERS = 2
cfg.MODEL.WEIGHTS = "detectron2://COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_3x/137849600/model_final_f10217.pkl"  # Let training initialize from model zoo
#cfg.MODEL.WEIGHTS = "detectron2://COCO-InstanceSegmentation/mask_rcnn_R_101_FPN_3x/138205316/model_final_a3ec72.pkl"  # Let training initialize from model zoo
cfg.SOLVER.IMS_PER_BATCH = 2
cfg.SOLVER.BASE_LR = 0.01 # pick a good LR
cfg.SOLVER.MAX_ITER = 1000    # 300 iterations seems good enough for this toy dataset; you may need to train longer for a practical dataset
cfg.MODEL.ROI_HEADS.BATCH_SIZE_PER_IMAGE = 128   # faster, and good enough for this toy dataset (default: 512)
cfg.MODEL.ROI_HEADS.NUM_CLASSES = 1  # only has one class (Hindi Words)

os.makedirs(cfg.OUTPUT_DIR, exist_ok=True)
trainer = DefaultTrainer(cfg) 
trainer.resume_or_load(resume=False)
trainer.train()

# Commented out IPython magic to ensure Python compatibility.
# %reload_ext tensorboard
# %tensorboard --logdir output
#!kill 1201

cfg.MODEL.WEIGHTS = os.path.join(cfg.OUTPUT_DIR, "model_final.pth")
cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.3   # set the testing threshold for this model
cfg.DATASETS.TEST = ("basepath_Val", )
os.makedirs(cfg.OUTPUT_DIR, exist_ok=True)
predictor = DefaultPredictor(cfg)

p1 = '/content/Synthetic Train Set - Detection & Recognition/Train/Image'
x = 0
for i in os.listdir(p1):
  x = x + len(os.listdir(p1+'/'+i)) 

print(x)

from detectron2.utils.visualizer import ColorMode
dataset_dicts = get_dicts("/content/Synthetic Train Set - Detection & Recognition/Val")
for d in random.sample(dataset_dicts, 3):    
    im = cv2.imread(d["file_name"])
    outputs = predictor(im)
    v = Visualizer(im[:, :, ::-1],
                   metadata=My_metadata, 
                   scale=0.8, 
                   instance_mode=ColorMode.IMAGE_BW   # remove the colors of unsegmented pixels
    )
    v = v.draw_instance_predictions(outputs["instances"].to("cpu"))
    cv2_imshow(v.get_image()[:, :, ::-1])

from detectron2.evaluation import COCOEvaluator, inference_on_dataset
from detectron2.data import build_detection_test_loader
evaluator = COCOEvaluator("basepath_Val", cfg, False, output_dir="./output/")
val_loader = build_detection_test_loader(cfg, "basepath_Val")
inference_on_dataset(trainer.model, val_loader, evaluator)

print(dataset_dicts[0])