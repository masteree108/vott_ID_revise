import tkinter as Tk
import os              
import sys 
import argparse
import matplotlib
#from numpy import arange, sin, pi
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk as NavigationToolbar2TkAgg
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure

# customize class for dealing with VoTT file,save log file,  SIFT feature extraction and feature matching(multi-processing)
import read_vott_id_json as RVIJ
import write_vott_id_json as WVIJ
import tool_display as TD
#import mulit_ID_process as MIP
#import cv_tracker as CVTR
#import process_project_vott as PPV
import log as PYM
#from main_func import*
import threading
import time



def read_user_input_info():
    ap = argparse.ArgumentParser()
    ap.add_argument("-p", "--prototxt", required=True,                                                                                                            
        help="path to Caffe 'deploy' prototxt file")
    ap.add_argument("-m", "--model", required=True,
        help="path to Caffe pre-trained model")
    ap.add_argument("-v", "--video", required=True,
        help="path to input video file")
    ap.add_argument("-o", "--output", type=str,
        help="path to optional output video file")
    ap.add_argument("-c", "--confidence", type=float, default=0.2,
        help="minimum probability to filter weak detections")
    args = vars(ap.parse_args())
     
    return args

def main():
    td.display_main_loop()
    pym.PY_LOG(True, 'D', py_name, "over")


if __name__ == '__main__':
    # construct the argument parser and parse the arguments
    #args = read_user_input_info()
    py_name = '< ID_revise >'

    # class init
    pym = PYM.LOG(True)
    pym.PY_LOG(False, 'D', py_name, 'start init')
    td = TD.tool_display()

    main()
    # load our serialized model from disk                                   
    #mc = mtc.mot_class(args)
    #mc.tracking(args)
