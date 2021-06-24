import os
import sys
import json
import enum
import threading
import queue
import numpy as np
import shutil
import operate_vott_id_json as OVIJ
import cv_sift_match as CSM
import log as PYM
from tkinter import *
from tkinter import messagebox
import tkinter.font as font
from multiprocessing import shared_memory
import cv2
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

class feature_match_process(threading.Thread):
# private
    __log_name = '< class feature_match_process>'
    __ovij_list = []
    __all_json_file_list_org = []
    __all_json_file_list_ok = []
    __amount_of_ovij = 0
    __file_process_path = './file_process/' 
    __file_path = ''
    __video_path = ''
    __vott_set_fps = 0
    __set_font = font.Font(name='TkCaptionFont', exists=True)
    __CSM_exist = False
    __debug_img_path = './debug_img/'
    __debug_img_sw = 1
    #__share_array_name = 'image'
    __share_array_name = 'new_id'

    def __copy_all_json_file(self):
        if os.path.isdir(self.__file_process_path) != 0:
            shutil.rmtree(self.__file_process_path)

        os.mkdir(self.__file_process_path)
        for path in self.__all_json_file_list_org: 
            shutil.copyfile(self.__file_path + "/" + path, self.__file_process_path + path)

    def __check_json_file_name(self):
        # if file name is not equal xxxx...xxx-asset.json,it will kick out to list
        temp = []
        for name in self.__all_json_file_list_org:
            #self.pym.PY_LOG(False, 'D', self.__log_name, "__check_json_file_name: " + name)
            if name.find("-asset.json")!=-1:
                temp.append(name)

        self.pym.PY_LOG(False, 'D', self.__log_name, "all json file checked ok ")
        if len(temp) != 0: 
            self.__all_json_file_list_org = []
            self.__all_json_file_list_org = temp.copy()
            # print all filename in the list
            for i in self.__all_json_file_list_org:
                self.pym.PY_LOG(False, 'D', self.__log_name, i)
            return 0
        else:
            return -1


    def __list_all_json_file(self, path):
        self.pym.PY_LOG(False, 'D', self.__log_name, 'msg(file_path): ' + path)
        self.__all_json_file_list_org = os.listdir(path)
        return self.__check_json_file_name()
            
        # print all filename in the list
        #for i in self.__all_json_file_list_org:
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

    def __create_debug_img_folder(self):
        if os.path.isdir(self.__debug_img_path) != 0:
            # folder existed
            shutil.rmtree(self.__debug_img_path)
        os.mkdir(self.__debug_img_path)


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

    def __find_timestamp_index_at_target_frame(self, index):
        first_timestamp = self.__ovij_list[index].get_timestamp()
        first_timestamp_sec = int(first_timestamp)
        diff = first_timestamp - first_timestamp_sec
        self.pym.PY_LOG(False, 'D', self.__log_name, 'target timestamp diff:%s' % diff)
        index = self.cvSIFTmatch.timestamp_index(self.__vott_set_fps, diff)
        return index

    def __get_cur_frame_index(self):
        index = self.__find_timestamp_index_at_target_frame(0)
        cur_index = int(self.__vott_set_fps)-index
        self.pym.PY_LOG(False, 'D', self.__log_name, 'cur_index:%s' % str(cur_index))
        return cur_index

    def __capture_frame_and_save_bboxes(self, index, next_state):
        timestamp = self.__ovij_list[index].get_timestamp()
        bboxes = self.__ovij_list[index].get_boundingBox()
        self.pym.PY_LOG(False, 'D', self.__log_name, 'timestamp:%s' % str(timestamp))
        #self.pym.PY_LOG(False, 'D', self.__log_name, 'bboxes:%s' % str(bboxes))
        self.cvSIFTmatch.capture_frame_and_save_bboxes(timestamp, bboxes, self.__ovij_list[index].get_ids(), next_state)


    def __deal_with_run_feature_match_command(self, msg):
        self.pym.PY_LOG(False, 'D', self.__log_name, '__deal_with_run_feature_match_command')

        if self.__debug_img_sw == 1:
            self.__create_debug_img_folder()
        
        # make sure file_process folder is existed
        if os.path.isdir(self.__file_process_path) != 0:
            # if it has all json file list we don't need to deal with those list again
            if len(self.__all_json_file_list_ok) == 0:
                self.__all_json_file_list_ok = os.listdir(self.__file_process_path)

                # creates ovij_list[]
                self.__amount_of_ovij = len(self.__all_json_file_list_ok)

                self.__create_ovij_list()
                
                drop_list = []
                drop_ovij_list = []
                # read json data and fill into ovij_list[num]
                for i in range(self.__amount_of_ovij):
                    if self.__ovij_list[i].read_all_file_info(self.__file_process_path, self.__all_json_file_list_ok[i]) == -1:
                        drop_list.append(self.__all_json_file_list_ok[i])
                        drop_ovij_list.append(self.__ovij_list[i])

                # check if those data are empty just dropping it
                for i,name in enumerate(drop_list):
                    self.pym.PY_LOG(False, 'D', self.__log_name, 'drop:%s' % name)
                    self.__all_json_file_list_ok.remove(name)
                    self.__ovij_list.remove(drop_ovij_list[i])
                    os.remove(self.__file_process_path + name)
                    self.__amount_of_ovij = len(self.__all_json_file_list_ok)
            
                # sort ovij_list by timestamp
                self.__sort_ovij_list()


                # FPS judgement
                self.__vott_set_fps = self.__judge_vott_set_fps()

                frame_size = self.__ovij_list[0].get_video_size()
                self.pym.PY_LOG(False, 'D', self.__log_name, 'cur frame_size:%s' % str(frame_size))

                # create cv_SIFT_match object
                self.__video_path = self.__ovij_list[0].get_parent_path()
                self.pym.PY_LOG(False, 'D', self.__log_name, 'video path:%s' % self.__video_path)
                self.cvSIFTmatch = CSM.cv_sift_match(self.__video_path, self.__vott_set_fps, frame_size, self.__debug_img_path, self.__debug_img_sw)
                self.__CSM_exist = True
                
            # hit run button only dealing with vott_set_fps *2 frames 
            
            # dealing with last frame at current second
            next_state = 0
            cur_index = self.__get_cur_frame_index()
            self.__capture_frame_and_save_bboxes(cur_index, next_state)
            self.cvSIFTmatch.crop_people_on_frame(next_state)

            cur_12_unit_size = self.cvSIFTmatch.get_crop_objects_12_unit_size(next_state)
            for i in range(cur_12_unit_size):
                self.cvSIFTmatch.make_ids_img_table(next_state, i)

            # dealing with frist frame at next second
            next_state = 1
            self.__capture_frame_and_save_bboxes(cur_index+1, next_state)
            self.cvSIFTmatch.crop_people_on_frame(next_state)
            next_12_unit_size = self.cvSIFTmatch.get_crop_objects_12_unit_size(next_state)
            for i in range(next_12_unit_size):
                self.cvSIFTmatch.make_ids_img_table(next_state, i)
                # make ids img table and send msg by queue to notify tool_display to read below img
                # self.cvSIFTmatch.save_no_ids_img_table(next_state,i)

            #combine two image tables
            # make current and next image table and send msg by queue to notify tool_display to read below img
            self.cvSIFTmatch.combine_cur_next_img()

            # feature extraction
            next_state = 0
            self.cvSIFTmatch.feature_extraction(next_state) 
            next_state = 1
            self.cvSIFTmatch.feature_extraction(next_state) 

            # next frame people to match current frame people
            self.shm_id[0] = next_12_unit_size 
            self.shm_id[1] = 1  #state
            for i, next_id in enumerate(self.__ovij_list[cur_index+1].get_ids()):
                cur_id, index = self.cvSIFTmatch.feature_matching_get_new_id(next_id)
                # below if is judging next frame person which one who is same as current frame person
                if cur_id != 'no_id':
                    self.pym.PY_LOG(False, 'D', self.__log_name, 'next frame id:%s identifies to current frame id:%s' % (next_id,cur_id))
                    self.shm_id[i+2] = cur_id

                else:
                    # show image and messagebox to notify user manually to type this id who cannot identify
                    self.shm_id[i+2] = '???'
                    self.pym.PY_LOG(False, 'D', self.__log_name, 'id:%s cannot identify' % next_id)

            msg = 'match_ok:'
            self.td_queue.put(msg)

            #msg = 'show_next_no_ids_img_table:'
            msg = 'show_combine_img_table:'
            self.td_queue.put(msg)

            self.cvSIFTmatch.show_ids_img_table(0)

            # waiting for too_display process write revise id data to shared memory
            while True:
                self.cvSIFTmatch.wait_key(1)
                if self.shm_id[1] == 0:
                    break
                
            self.cvSIFTmatch.destroy_window()
            # finished 2 secs so reorganize those list we need
            
        else:
            self.show_info_msg_on_toast("error", "請先執行選擇json檔案來源資料夾")
            self.pym.PY_LOG(True, 'E', self.__log_name, 'There are no file_process folder!!')
            self.shut_down_log("over")
# public
    #def __init__(self, fm_process_que, td_que, gd_que, shm_name, shm_size):
    def __init__(self, fm_process_que, td_que, shm_name, shm_size):
        self.__set_font.config(family='courier new', size=15)
        threading.Thread.__init__(self)
        self.fm_process_queue = fm_process_que
        self.td_queue = td_que
        self.pym = PYM.LOG(True)
        self.pym.PY_LOG(False, 'D', self.__log_name, 'init')
        #self.gd_queue = gd_que
        self.shm_id = shared_memory.ShareableList(name=shm_name)

    def __del__(self):
        #deconstructor
        self.shut_down_log("over")
        self.shm_id.shm.close()

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

