import os
import sys
import json
import enum
import threading
import queue
import numpy as np
import shutil
import math

import operate_vott_id_json as OVIJ
import cv_sift_match as CSM
import log as PYM
from tkinter import *    
from tkinter import messagebox
import tkinter.font as font

'''
command from tool_display process:
json_file_path:
    (1) copy file to ./file_process folder
run_feature_match:
    (1) load data into every ovij class
    (2) sort ovij_list
    (3) VoTT set FPS judgement
    (4) init cv_sift_match
    (5) load video to ovih_class[fps-1] timestamp, to cut every person image and save to id_img  
'''

'''
class BBOX_ITEM(enum.Enum):
    height = 0
    width = 1
    left = 2
    top = 3

class VIDEO_SIZE(enum.Enum):
    W = 0
    H = 1
'''

class feature_match_process(threading.Thread):
# private
    __log_name = '< class feature_match_process>'
    __ovij_list = []
    __all_json_file_list = []
    __amount_of_ovij = 0
    __file_process_path = './file_process/' 
    __file_path = ''
    __video_path = ''
    __vott_set_fps = 0
    __set_font = font.Font(name='TkCaptionFont', exists=True)
    __CSM_exist = False

    def __copy_all_json_file(self):
        if os.path.isdir(self.__file_process_path) != 0:
            shutil.rmtree(self.__file_process_path)

        os.mkdir(self.__file_process_path)
        for path in self.__all_json_file_list: 
            shutil.copyfile(self.__file_path + "/" + path, self.__file_process_path + path)

    def __check_json_file_name(self):
        # if file name is not equal xxxx...xxx-asset.json,it will kick out to list
        temp = []
        for name in self.__all_json_file_list:
            #self.pym.PY_LOG(False, 'D', self.__log_name, "__check_json_file_name: " + name)
            if name.find("-asset.json")!=-1:
                temp.append(name)

        self.pym.PY_LOG(False, 'D', self.__log_name, "all json file checked ok ")
        if len(temp) != 0: 
            self.__all_json_file_list = []
            self.__all_json_file_list = temp.copy()
            # print all filename in the list
            for i in self.__all_json_file_list:
                self.pym.PY_LOG(False, 'D', self.__log_name, i)
            return 0
        else:
            return -1


    def __list_all_json_file(self, path):
        self.pym.PY_LOG(False, 'D', self.__log_name, 'msg(file_path): ' + path)
        self.__all_json_file_list = os.listdir(path)
        return self.__check_json_file_name()
            
        # print all filename in the list
        #for i in self.__all_json_file_list:
            #self.pym.PY_LOG(False, 'D', self.__log_name, i)

    def __create_ovij_list(self):
        self.pym.PY_LOG(False, 'D', self.__log_name, 'amount of ovij: %s' % str(self.__amount_of_ovij))
        for i in range(self.__amount_of_ovij):
            ovij = ''
            ovij = OVIJ.operate_vott_id_json()
            self.__ovij_list.append(ovij)

    def __sort_ovij_list(self):
        temp_no_sort = []
        temp_ovij_list = []
        for i in range(self.__amount_of_ovij):
            temp_no_sort.append(self.__ovij_list[i].get_timestamp())
            self.pym.PY_LOG(False, 'D', self.__log_name, 'timestamp without sort %s' % str(temp_no_sort[i]))
        temp_sort = temp_no_sort.copy()
        temp_sort.sort() 
        #for i in range(self.__amount_of_ovij):
            #self.pym.PY_LOG(False, 'D', self.__log_name, 'timestamp with sort %s' % str(temp_sort[i]))

        find_index = np.array(temp_no_sort)
        # sort ovij_list-method0
        for i, tps in enumerate(temp_sort):
            index = np.argwhere(find_index == tps)
            temp_ovij_list.append(self.__ovij_list[int(index)])
        '''
        # sort ovij_list-method1 equal above sort ovij_list-method0
        for i, tps in enumerate(temp_sort):
            for j, tpns in enumerate(temp_no_sort):
                if tps == tpns:
                    print("tps:%s"% str(tps)+' '+str(i))
                    print("tpns:%s"% str(tpns)+' '+str(j))
                    temp_ovij_list.append(self.__ovij_list[j])
                    break
        '''
        self.__ovij_list = []
        self.__ovij_list = temp_ovij_list.copy()
        for i in range(self.__amount_of_ovij):
            self.pym.PY_LOG(False, 'D', self.__log_name, 'ovij_list with sort %s' % str(self.__ovij_list[i].get_timestamp()))

    def __judge_vott_set_fps(self):
        pre_timestamp = self.__ovij_list[0].get_timestamp()
        cur_timestamp = self.__ovij_list[1].get_timestamp()
        vott_set_fps = 1 / (cur_timestamp - pre_timestamp)
        vott_set_fps = round(vott_set_fps, 1) 
        self.pym.PY_LOG(False, 'D', self.__log_name, 'vott_set_fps %s' % str(vott_set_fps))
        return vott_set_fps

    def __deal_with_json_file_path_command(self, msg):
        self.__file_path = msg[15:]
        if self.__list_all_json_file(self.__file_path) == 0:
            self.pym.PY_LOG(False, 'D', self.__log_name, '__deal_with_json_file_path_command')
            #copy all of json data to ./process data folder
            self.__copy_all_json_file()
            self.show_info_msg_on_toast("提醒","初始化完成,請執行 run 按鈕")
        else:
            self.show_info_msg_on_toast("error", "此資料夾沒有 *.json 檔案")
            self.pym.PY_LOG(True, 'E', self.__log_name, 'There are no any *.json files')
            self.shut_down_log("over")

    def __every_sec_last_timestamp_check(self):

        first_timestamp = self.__ovij_list[0].get_timestamp()
        first_timestamp_sec = int(first_timestamp)
        diff = first_timestamp - first_timestamp_sec
        self.pym.PY_LOG(False, 'D', self.__log_name, 'first_timestamp diff:%s' % diff)
        index = self.cvSIFTmatch.timestamp_index(self.__vott_set_fps, diff)
        return index
        #return self.__ovij_list[int(self.__vott_set_fps)-index].get_timestamp()

    def __deal_with_run_feature_match_command(self, msg):
        self.pym.PY_LOG(False, 'D', self.__log_name, '__deal_with_run_feature_match_command')

        # make sure file_process folder is existed
        if os.path.isdir(self.__file_process_path) != 0:
            self.__all_json_file_list = os.listdir(self.__file_process_path)
            # creates ovij_list[]
            self.__amount_of_ovij = len(self.__all_json_file_list)

            self.__create_ovij_list()

            # read json data and fill into ovij_list[num]
            for i in range(self.__amount_of_ovij):
                print(self.__all_json_file_list[i])
                self.__ovij_list[i].read_all_data_info(self.__file_process_path, self.__all_json_file_list[i])
            
            # sort ovij_list by timestamp
            self.__sort_ovij_list()

            # FPS judgement
            self.__vott_set_fps = self.__judge_vott_set_fps()

            # create cv_SIFT_match object
            self.__video_path = self.__ovij_list[0].get_parent_path()
            self.pym.PY_LOG(False, 'D', self.__log_name, 'video path:%s' % self.__video_path)
            self.cvSIFTmatch = CSM.cv_sift_match(self.__video_path, self.__vott_set_fps)
            self.__CSM_exist = True
            
            # find last timestamp at first frame second
            index = self.__every_sec_last_timestamp_check()
            cur_index = int(self.__vott_set_fps)-index
            self.pym.PY_LOG(False, 'D', self.__log_name, 'cur_index:%s' % str(cur_index))
            cur_timestamp = self.__ovij_list[cur_index].get_timestamp()
            bboxes = self.__ovij_list[cur_index].get_boundingBox()
            frame_size = self.__ovij_list[cur_index].get_video_size()
            self.pym.PY_LOG(False, 'D', self.__log_name, 'timestamp:%s' % str(cur_timestamp))
            self.pym.PY_LOG(False, 'D', self.__log_name, 'frame_size:%s' % str(frame_size))
            self.pym.PY_LOG(False, 'D', self.__log_name, 'cur_bboxes:%s' % str(bboxes))
            self.cvSIFTmatch.video_settings(cur_timestamp, bboxes, frame_size)

        else:
            self.show_info_msg_on_toast("error", "請先執行選擇json檔案來源資料夾")
            self.pym.PY_LOG(True, 'E', self.__log_name, 'There are no file_process folder!!')
            self.shut_down_log("over")

# public
    def __init__(self, fm_process_que, td_que):
        self.__set_font.config(family='courier new', size=15)
        threading.Thread.__init__(self)
        self.fm_process_queue = fm_process_que
        self.td_queue = td_que
        self.pym = PYM.LOG(True)
        self.pym.PY_LOG(False, 'D', self.__log_name, 'init')
        
    def FMP_main(self, msg):
        self.pym.PY_LOG(False, 'D', self.__log_name, 'receive msg from queue: ' + msg)
        if msg[:15] == "json_file_path:":
            self.__deal_with_json_file_path_command(msg)
        
        elif msg == "run_feature_match":
            self.__deal_with_run_feature_match_command(msg)     

    def run(self):
        self.pym.PY_LOG(False, 'D', self.__log_name, 'run')
        while True:
            msg = self.fm_process_queue.get()
            self.FMP_main(msg)
            if msg == 'over':
                break
        self.shut_down_log("fm_rpocess_over")

    def shut_down_log(self, msg):
        self.pym.PY_LOG(True, 'D', self.__log_name, msg)

        # delete all ovij_list's pym process
        amt_ovij_list = len(self.__ovij_list)
        if amt_ovij_list != 0:
            for i in range(amt_ovij_list):
                self.__ovij_list[i].shut_down_log("%d pym over" %i)  

        # delete cv_sift_match's pym process
        if self.__CSM_exist == True:
            self.cvSIFTmatch.shut_down_log("over")

    def show_error_msg_on_toast(self, title, msg):
        messagebox.showerror(title, msg)

    def show_info_msg_on_toast(self, title, msg):
        messagebox.showinfo(title, msg)
