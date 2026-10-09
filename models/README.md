YOLOv3-Tiny Model Files

The humanoid interaction program uses OpenCV's DNN module with the YOLOv3-Tiny object detection model.

Required Files

Download and prepare these files:

* 'yolov3-tiny.cfg' — network configuration
* 'yolov3-tiny.weights' — pretrained model weights
* 'coco.names' — COCO object class labels

Setup Instructions

1. Download the configuration and class-label files from the official YOLO/Darknet project sources.
2. Obtain the matching pretrained weights from the linked model source.
3. Place the files in this 'models' directory.
4. Update the file paths in 'humanoid_interaction.py' to point to the 'models' directory.

Notes

The pretrained weights are not included in this repository. Check the source project's licensing and usage terms before redistributing model files.
The program requires all three files to be present at the configured paths before it can initialize the object detector.
