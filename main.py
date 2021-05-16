import tkinter as Tk
import os              
import sys 
import matplotlib

# customize class for dealing with VoTT file,save log file,  SIFT feature extraction and feature matching
import read_vott_id_json as RVIJ
import write_vott_id_json as WVIJ
import tool_display as TD
import feature_match_process as FMP
#import mulit_ID_process as MIP
#import cv_tracker as CVTR
#import process_project_vott as PPV
import log as PYM
#from main_func import*
import threading
import time
import queue


def close_all_process(pym, fm_process_queue):
    pym.PY_LOG(True, 'D', py_name, "over")
    fm_process_queue.put("over")


def main(td_queue, fm_process_queue):
    # processing thread
    fm_process.start()
    
    # tool display thread
    td.display_main_loop()

    # finished
    close_all_process(pym, fm_process_queue)

if __name__ == '__main__':
    py_name = '< main >'

    #td_lock = threading.Lock()
    td_queue = queue.Queue()
    fm_process_queue = queue.Queue()
    
    # class init
    pym = PYM.LOG(True)
    pym.PY_LOG(False, 'D', py_name, 'start init')
    td = TD.tool_display(td_queue, fm_process_queue)
    fm_process = FMP.feature_match_process(fm_process_queue, td_queue) 
    main(td_queue, fm_process_queue)
