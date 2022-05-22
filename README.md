---
title: 'Assist in comparing VoTT JSON files with the Integration tracker ID tool (English)'
disqus: hackmd
---
Assist in comparing VoTT JSON files with the Integration tracker ID tool (English)
===



[TOC]

[It is recommended to watch the README here](https://hackmd.io/@NTUTVOTT/r1OMg-Nw5)

## Version information
Version：v0.0.1
Environment: window10 、ubuntu 20.0


## 1. Description of documents
### Tools Introduction
Introduce **Assist in comparing VoTT JSON files with the Integration tracker ID tool**.This tool can be used to assist in modifying the situation that different users label the same video and the tracking object ID is "tags" differently.Without this tool, the user can only modify the ID within VoTT frame by frame,as shown in Figure 1 below. It will cause too much human resource. In addition, from the perspective of UAV, it is difficult to label too small characters,  which undoubtedly increases the workload of the label modifier


If you do not use this tool, the user must manually modify the ID at the video junction.

![](https://i.imgur.com/PWl9WBR.png)

**Figure 1 Modify ID in VoTT**

## 2. Data pre - processing and comparison mode architecture description
### (1) Data preprocessing and comparison mode architecture diagram
As shown in Figure 2 below, in the part of image pre-processing, the figure pixel is too small due to the perspective of UAV.If there is no image pre-processing for comparison, the matching effect will be poor because of fewer feature points. In addition, the tool display screen needs to be manually detected again as shown in Figure 3 below, if the image size is directly adjusted, the image distortion will be caused, as shown in Figure 4 below. Therefore, the image must be pre-processed by super Resolution and Detail Ehance first. In addition, for match method, please refer to (2) Verification and results of comparison method


![](https://i.imgur.com/FjbcTRJ.png)
**Figure 2 Architecture diagram**


![](https://i.imgur.com/0vO0UFL.jpg)
**Figure 3 Tool detects character screen**

 ![](https://i.imgur.com/dxKHkXZ.png)
**Figure 4 Zooming in on the image will be blurry**


### (2) Verification and results of comparison method
The following description uses five figures (ID_001 to ID_005) for comparison, as shown in Figure 5 below
**Figure 5 Comparative person information**
![](https://i.imgur.com/YgKDLpL.png)

**Table 1 Test result**
item 4 is the best one
![](https://i.imgur.com/W4mmRhV.png)

## 3. Program architecture
This tool uses a graphical interface, so it needs to use Python's Tkinter. In addition, it has its own class for dealing with character match, JSON file processing and system action sequence (Excel file)
```
1. main.py: 
Manages calss:tool_display and class: Feature_match_process

2. tool_display.py: 
Responsible for display screen and button event processing
Queue and shared memory are used to communicate with processes of 
Feature_match_process

3. feature_match_process.py：
Queue and shared memory are used to communicate with processes of 
Feature_match_process

Managing class: operate_vott_id_JSON Handles reads and writes to JSON data 
(as shown in Figure 6 below)

Manage class: CV_SIFt_match for character capture, image pre-processing 
and ID comparison and correction

Manage class:system_file to store the system information required 
by the tool and store the results in excel files (as shown in Figure 6 below).


All of the above classes are stored as log by class:log.py, and all logs will be 
aggregated into result/log.txt
The above description is as shown in figure 7 below


```

**Figure 6 Feature_match_process uses class:operate_vott_id_json to read all json files (only timestamp and asset-id). The data is organized into processing information and stored in Excel using class: System_file, so that the system only needs to import the required JSON data in excel order**

![](https://i.imgur.com/fPZrrrf.png)

**Figure 7 program architecture**
![](https://i.imgur.com/XAyKyKd.png)



## 4. Environment and Setup
Since use Python to program, So user must have Anaconda installed
If you are not familiar with anaconda installation, refer to this article
[Python Environment Setup](https://hackmd.io/@NTUTVOTT/SJMXCwn0P)

The following contains all the necessary package. Follow the steps below to install and set them up

#### （1）Screen resolution
Set Resolution in Scale and Layout to 1920*1080, and change the size of text,apps and other items to 100%(this setting unchanged may cause tool display error)
![](https://i.imgur.com/qRukXKD.png)

#### （2）Python environment

```gherkin=
conda create -n opencv4.5 python=3.8
```
#### （3）Switch to the opencv4.5  environment
```gherkin=
conda activate opencv4.5
```
![](https://i.imgur.com/TCszR6s.png)

#### （4）Install necessary package

About the OpencV version, to find out what the current version is, use the following methods
Exit the Conda environment
```gherkin=
conda deactivate
```
Search Opencv Version
```gherkin=
pip install opencv-python== 
```
![](https://i.imgur.com/bW99jzp.png)

Switch to the Opencv4.5 environment and install the following package
```gherkin=
conda activate opencv4.5
pip install opencv-python==4.5.1.48
pip install opencv-contrib-python==4.5.1.48
pip install jupyterlab
pip install matplotlib
pip install sklearn
pip install scikit-image
pip install imutils
pip install tk
pip install shortuuid
(x)pip install pandas
pip install SharedArray
(x)pip install psutil
pip install easygui
pip install platform
```
## 5. Step

#### （1）Select the JSON for the video you want to modify
Select the CURRENT JSON file whose Id you want to modify, press the button and select the path

![](https://i.imgur.com/4gcmFEJ.png)

press "選擇json file來源資料"(source of JSON files folder) can not to see those JSON files,so you need to know where folder are saved those JSON files what you want.

![](https://i.imgur.com/PPnwkmE.png)

#### （2）Press "執行修正" to RUN autocorrection
After pressing "執行修正" and waiting, wait for the result window to appear.
![](https://i.imgur.com/B4CNAq1.png)

#### （3）Double check the effect of autocorrection
After jump out of the window, you can see that the tool automatically compares the same character and matches the Id. At this time, you need to confirm whether it is the same character:
Same character: Maintain the same Id.
Different characters: give yourself a new Id or match to the corresponding characters in the previous frame.


![](https://i.imgur.com/2xKslEO.png)

#### （4）Check that the same Id exists
When the Id appears the same, it needs to be modified to the new Id or matched to the corresponding character in the previous frame.
![](https://i.imgur.com/lRujt5x.png)

#### （5）When the number of people is different, confirm the reason
When a character appears in the current frame more than in the previous frame, you need to return VoTT or export a video to double confirm whether this character has a missing bounding in the previous frame. If there is a missing frame, please fill boundbox in VoTT.
![](https://i.imgur.com/tgP5qrJ.png)

#### （6）Confirm completed
Click "修正完成" to complete and complete more Id modify.
![](https://i.imgur.com/EShHzpm.png)

## 6. Demonstration video

[![IMAGE ALT TEXT](http://img.youtube.com/vi/11RW4ov7CC8/0.jpg)](https://www.youtube.com/watch?v=11RW4ov7CC8  "DEMO")

###### tags: `tool`
