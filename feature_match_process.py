import os
import sys
import json
import enum
import threading
import queue
import numpy as np
import shutil
import operate_vott_id_json as OVIJ
import system_file as SF
import cv_sift_match as CSM
import log as PYM
from tkinter import *
from tkinter import messagebox
import tkinter.font as font
from multiprocessing import shared_memory
import cv2
import pandas as pd
from time import sleep

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
    __all_file_list = []
    __amount_of_ovij = 0
    __system_file_path = './.system/'
    __file_process_path = './.system/file_process/' 
    __file_process_path_backup = './.system/file_process_backup/' 
    __finished_files_path = './result/finished_files/' 
    __finished_round_path = './result/finished_round' 
    __file_path = ''
    __video_path = ''
    __vott_set_fps = 0
    __set_font = font.Font(name='TkCaptionFont', exists=True)
    __debug_img_path = './result/debug_img/'
    __debug_img_sw = 1
    __share_array_name = 'new_id'
    __already_init = False
    __excel_path = './result/'
    __interval = 1
    __sys_file = None
    __cal_amount_of_json = 0
    __cur_target_index = 0
    __this_round_end_index = 0
    __cvSIFTmatch = None

    def __move_this_round_json_file(self, round_num, move_json_list):
        if os.path.isdir(self.__finished_files_path) == 0:
            os.makedirs(self.__finished_files_path)

        round_folder_path = self.__finished_round_path + '_'+ str(round_num) + '/'
        self.pym.PY_LOG(False, 'D', self.__log_name, 'round_path:%s' % round_folder_path)
        if os.path.isdir(round_folder_path) == 0:
            os.makedirs(round_folder_path)

        for i,file_name in enumerate(move_json_list): 
            self.pym.PY_LOG(False, 'D', self.__log_name, 'move_json_list[%d]:' % i)
            self.pym.PY_LOG(False, 'D', self.__log_name,  file_name)
            shutil.copyfile(self.__file_process_path + file_name, self.__finished_files_path + file_name)
            shutil.copyfile(self.__file_process_path + file_name, round_folder_path + file_name)
            shutil.copyfile(self.__file_process_path + file_name, self.__file_process_path_backup + file_name)
            sleep(0.05)
            # remain the last one json at this round
            if i != (len(move_json_list)-1):
                os.remove(self.__file_process_path + file_name)
            else:
                # below()==1 that expresses only left one json in the folder,so we don't need to remain it as usual
                if len(os.listdir(self.__file_process_path)) == 1:
                    os.remove(self.__file_process_path + file_name)

    def __copy_all_json_file(self):
        '''
        if os.path.isdir(self.__file_process_path) != 0:
            shutil.rmtree(self.__file_process_path)
        
        if os.path.isdir(self.__file_process_path_backup) != 0:
            shutil.rmtree(self.__file_process_path_backup)
        '''
        if os.path.isdir(self.__system_file_path):
            shutil.rmtree(self.__system_file_path)

        os.makedirs(self.__file_process_path)
        os.makedirs(self.__file_process_path_backup)
        for file_name in self.__all_file_list: 
            shutil.copyfile(self.__file_path + "/" + file_name, self.__file_process_path + file_name)
            shutil.copyfile(self.__file_path + "/" + file_name, self.__file_process_path_backup + file_name)

    def __check_json_file_name(self):
        # if file name is not equal xxxx...xxx-asset.json,it will kick out to list
        temp = []
        for file_name in self.__all_file_list:
            #self.pym.PY_LOG(False, 'D', self.__log_name, "__check_json_file_name: " + name)
            root, extension = os.path.splitext(file_name)
            if extension == '.json':      
                if file_name.find("-asset.json")!=-1:
                    temp.append(file_name)

        self.pym.PY_LOG(False, 'D', self.__log_name, "all json file checked ok ")
        if len(temp) != 0: 
            self.__all_file_list = []
            self.__all_file_list = temp.copy()
            # print all filename in the list
            for i in self.__all_file_list:
                self.pym.PY_LOG(False, 'D', self.__log_name, i)
            return 0
        else:
            return -1


    def __list_all_file(self, path):
        self.pym.PY_LOG(False, 'D', self.__log_name, 'msg(file_path): ' + path)
        self.__all_file_list = os.listdir(path)
        amount_of_file = len(self.__all_file_list)
        self.pym.PY_LOG(False, 'D', self.__log_name, 'amount_of_file:%d' % amount_of_file)
        return self.__check_json_file_name()

    def __create_ovij_list_and_read_json_content(self):
    
        self.pym.PY_LOG(False, 'D', self.__log_name, 'self.__cur_target_index:%d' % self.__cur_target_index)
        self.pym.PY_LOG(False, 'D', self.__log_name, 'self.__this_round_end_index:%d' % self.__this_round_end_index)
        self.__ovij_list = []
        json_list = []
        json_list = self.__sys_file.read_this_round_json_list(self.__cur_target_index, self.__this_round_end_index)
        for i,asset_id in enumerate(json_list):
            ovij = ''
            ovij = OVIJ.operate_vott_id_json()
            ovij.read_all_file_info(self.__file_process_path,  asset_id)
            self.__ovij_list.append(ovij)

    def __create_debug_img_folder(self):
        if os.path.isdir(self.__debug_img_path) != 0:
            # folder existed
            shutil.rmtree(self.__debug_img_path)
        os.makedirs(self.__debug_img_path)


    def __deal_with_json_file_path_command(self, msg):
        self.__file_path = msg[15:]
        if self.__list_all_file(self.__file_path) == 0:
            self.pym.PY_LOG(False, 'D', self.__log_name, '__deal_with_json_file_path_command')
            # copy all of json data to ./process data folder
            self.__copy_all_json_file()
            
            # init class system_file
            self.__sys_file =  SF.system_file(self.__file_path, self.__all_file_list, "create_excel")
            
            self.__sys_file.id_and_timestamp_fill_into_excel()

            self.show_info_msg_on_toast("提醒","初始化完成,請執行 run 按鈕")
            self.__already_init = True
        else:
            self.show_info_msg_on_toast("error", "此資料夾沒有 *.json 檔案")
            self.pym.PY_LOG(True, 'E', self.__log_name, 'There are no any *.json files')
            self.shut_down_log("over")
    
    def __capture_frame_and_save_bboxes(self, index, next_state):
        timestamp = self.__ovij_list[index].get_timestamp()
        bboxes = self.__ovij_list[index].get_boundingBox()
        self.pym.PY_LOG(False, 'D', self.__log_name, 'timestamp:%s' % str(timestamp))
        #self.pym.PY_LOG(False, 'D', self.__log_name, 'bboxes:%s' % str(bboxes))
        self.__cvSIFTmatch.capture_frame_and_save_bboxes(timestamp, bboxes, self.__ovij_list[index].get_ids(), next_state)
    
    def __notify_tool_display_process_file_exist(self):
        msg = 'file_exist:'
        self.td_queue.put(msg)

    def __notify_tool_display_process_file_not_exist(self):
        msg = 'file_not_exist:'
        self.td_queue.put(msg)
        self.pym.PY_LOG(False, 'D', self.__log_name, 'there no any files in the folder')

    def __notify_tool_display_process_file_too_few(self):
        msg = 'file_too_few:'
        self.td_queue.put(msg)
        self.pym.PY_LOG(False, 'D', self.__log_name, 'amount of json file are too few')

    def __check_amount_of_json_enough(self):
        left_amount_of_json = self.__sys_file.read_left_amount_of_json()
        fps = self.__vott_set_fps
        
        if left_amount_of_json == 0:
            return False

        if self.__sys_file.is_first_load_json() == True:
            # we must - first_timestamp_index becasue we don't know first_timestamp_index is or not equal 0 
            self.__cal_amount_of_json = int(self.__interval * fps * 2 - self.__sys_file.read_first_timestamp_index())
        else:
            self.__cal_amount_of_json = int(self.__interval * fps + 1)
            
        if self.__cal_amount_of_json <= left_amount_of_json:
            self.pym.PY_LOG(False, 'D', self.__log_name, 'cal_amount_of_json:%d' % self.__cal_amount_of_json)
            # check index is correct(if not correct will be calibrating) and get current frame target index and next frame target index
            self.__cur_target_index, self.__this_round_end_index = \
                                self.__sys_file.check_calibrate_index_and_get_cur_frame_target_index(self.__cal_amount_of_json)
            self.pym.PY_LOG(False, 'D', self.__log_name, 'after calibrated cal_amount_of_json:%d' % self.__cal_amount_of_json)

            return True
        else:
            return False
        

    def __deal_with_file_list(self):

        if self.__debug_img_sw == 1:
            self.__create_debug_img_folder()

        if self.__sys_file is None:
            self.__sys_file =  SF.system_file(self.__file_path, "", "")

        # get fps
        self.__vott_set_fps = self.__sys_file.read_vott_set_fps()

        # according to user typed interval value to judge the amount of json file is enough to use or not
        if self.__check_amount_of_json_enough() == False:
            return False
       
        self.__create_ovij_list_and_read_json_content()

        # create cv_SIFT_match object
        frame_size = self.__ovij_list[0].get_video_size()
        self.pym.PY_LOG(False, 'D', self.__log_name, 'cur frame_size:%s' % str(frame_size))

        self.__video_path = self.__ovij_list[0].get_parent_path()
        self.pym.PY_LOG(False, 'D', self.__log_name, 'video path:%s' % self.__video_path)
        self.__cvSIFTmatch = CSM.cv_sift_match(self.__video_path, self.__vott_set_fps, frame_size, self.__debug_img_path, self.__debug_img_sw)
        return True


    def __init_or_reload_relate_variable(self):
        self.pym.PY_LOG(False, 'D', self.__log_name, '__init_or_reload_relate_variable')
        self.__interval = 1 
        self.__cal_amount_of_json = 0
        self.__ovij_list = []

        # others variable to init
        # reload CSM class object
        self.__cvSIFTmatch.init_for_next_round()

    def __deal_with_run_feature_match_command(self):
        self.pym.PY_LOG(False, 'D', self.__log_name, '__deal_with_run_feature_match_command')

        # dealing with last frame at current second
        next_state = 0
        cur_index = 0
        self.pym.PY_LOG(False, 'D', self.__log_name, 'cur_index:%d' % cur_index)
        self.pym.PY_LOG(False, 'D', self.__log_name, 'ovij[%d].asset_id:' % cur_index)
        self.pym.PY_LOG(False, 'D', self.__log_name, self.__ovij_list[cur_index].get_asset_id())
        next_index = 1
        self.pym.PY_LOG(False, 'D', self.__log_name, 'next_index:%d' % next_index)
        self.pym.PY_LOG(False, 'D', self.__log_name, 'ovij[%d].asset_id:' % next_index)
        self.pym.PY_LOG(False, 'D', self.__log_name, self.__ovij_list[next_index].get_asset_id())

        self.__capture_frame_and_save_bboxes(cur_index, next_state)
        self.__cvSIFTmatch.crop_people_on_frame(next_state)

        cur_12_unit_size = self.__cvSIFTmatch.get_crop_objects_12_unit_size(next_state)
        for i in range(cur_12_unit_size):
            self.__cvSIFTmatch.make_ids_img_table(next_state, i)

        # dealing with frist frame at next second
        next_state = 1
        self.__capture_frame_and_save_bboxes(next_index, next_state)
        self.__cvSIFTmatch.crop_people_on_frame(next_state)
        next_12_unit_size = self.__cvSIFTmatch.get_crop_objects_12_unit_size(next_state)
        for i in range(next_12_unit_size):
            self.__cvSIFTmatch.make_ids_img_table(next_state, i)

        #combine two image tables
        # make current and next image table and send msg by queue to notify tool_display to read below img
        self.__cvSIFTmatch.combine_cur_next_img()
        
        # feature extraction
        next_state = 0
        self.__cvSIFTmatch.feature_extraction(next_state) 
        next_state = 1
        self.__cvSIFTmatch.feature_extraction(next_state) 

        # using IoU method to match(it's not a properly match method os disabled it)
        self.__cvSIFTmatch.IOU_check()

        # next frame people to match current frame people
        self.shm_id[0] = next_12_unit_size 
        self.shm_id[1] = 1  #state

        for i,next_id in enumerate(self.__cvSIFTmatch.next_frame_ids_list()):
            cur_id, index, match_point = self.__cvSIFTmatch.feature_matching_get_new_id(next_id)
            # show SIFT feature match number 
            self.pym.PY_LOG(False, 'D', self.__log_name, 'SIFT feture match point:%d' % match_point)
            # below if is judging next frame person which one who is same as current frame person
            if cur_id != 'no_id':
                self.pym.PY_LOG(False, 'D', self.__log_name, 'next frame id:%s identifies to current frame id:%s' % (next_id,cur_id))
            else:
                # show image and messagebox to notify user manually to type this id who cannot identify
                self.pym.PY_LOG(False, 'D', self.__log_name, 'id:%s cannot identify' % next_id)

        # using SIFT match method or IoU match method to determine recognition id at next frame
        self.__cvSIFTmatch.use_SIFT_or_IoU_to_determine_id()
        self.__cvSIFTmatch.show_final_predict_ids()
        for i in range(self.__cvSIFTmatch.read_amount_of_next_frame_people()):
            self.shm_id[i+2] = self.__cvSIFTmatch.read_final_predict_ids(i)

        msg = 'match_ok:'
        self.td_queue.put(msg)

        # bring cur and next frame amout of people in to below msg
        amount_of_cur_people = self.__ovij_list[cur_index].get_object_number()
        amount_of_next_people = self.__ovij_list[next_index].get_object_number()
        msg = 'show_combine_img_table:'+ str(amount_of_cur_people) + ';' + str(amount_of_next_people)
        self.td_queue.put(msg)

        self.__cvSIFTmatch.show_ids_img_table(0)

        # waiting for too_display process write revise id data to shared memory
        while True:
            self.__cvSIFTmatch.wait_key(1)
            if self.shm_id[1] == 0:
                break
            
        self.__cvSIFTmatch.destroy_window()

        # finished 2 secs so reorganize those list we need
        new_id_list = []
        for i in range(2,self.__cvSIFTmatch.read_amount_of_next_frame_people()+2):
            self.pym.PY_LOG(False, 'D', self.__log_name, 'new_id:' + self.shm_id[i])
            new_id_list.append(self.shm_id[i])
        
        # save new id to those json which needs to change id
        #for i,ovij in enumerate(self.__ovij_list):
        for i in range(next_index, len(self.__ovij_list)):
            self.__ovij_list[i].write_data_to_id_json_file(new_id_list)
            self.__ovij_list[i].update_ids(new_id_list)
            self.pym.PY_LOG(False, 'D', self.__log_name, 'update asset-id:%s' % self.__ovij_list[i].get_asset_id())
        
        
        done_json_index = self.__this_round_end_index
        self.pym.PY_LOG(False, 'D', self.__log_name, 'done_json_index:%d' % done_json_index)

        # get move *.json list
        move_json_list = []
        move_json_list = self.__sys_file.get_this_round_move_list(done_json_index)

        self.__sys_file.update_excel_sheet1(self.__cur_target_index, self.__this_round_end_index)
        round_num = self.__sys_file.update_excel_sheet3(self.__interval, self.__cur_target_index, done_json_index)
        self.__sys_file.update_excel_sheet2(self.__cur_target_index, done_json_index, 'N')
        
        # copy about cur json files and next json files(modified id success) to previous_compare_files folder
        self.__move_this_round_json_file(round_num, move_json_list)
        # copy excecl file
        excel_name = self.__ovij_list[0].get_parent_name()+"_result.xlsx"
        self.__sys_file.copy_excel_to_result_folder(self.__excel_path + excel_name)
        msg = excel_name
        self.td_queue.put(msg)
        self.__init_or_reload_relate_variable() 


    def __read_interval_from_msg(self, msg):
        index = msg.find(':') + 1
        self.__interval = int(msg[index:])
        self.pym.PY_LOG(False, 'D', self.__log_name, 'check_interval:%d' % self.__interval)


    def __move_previous_done_json_files_to_file_process_folder(self, json_list, first_round_json_list, round_num):
        round_path = self.__finished_round_path + '_' + str(round_num+1)
        if os.path.isdir(round_path) == True:
            shutil.rmtree(round_path)

        for i,file_name in enumerate(json_list):
            if i == 0:
                shutil.copyfile(self.__finished_files_path + file_name, self.__file_process_path + file_name)
            else:
                os.remove(self.__finished_files_path + file_name)
                shutil.copyfile(self.__file_process_path_backup + file_name, self.__file_process_path + file_name)

        if round_num - 1 == 0:
            for i,file_name in enumerate(first_round_json_list):
                shutil.copyfile(self.__file_process_path_backup + file_name, self.__file_process_path + file_name)
                

    def __run_resume_to_previous_state(self):
        self.pym.PY_LOG(False, 'D', self.__log_name, 'read_previous_step_start_and_end_index')
        round_num, cur_index, end_index = self.__sys_file.read_previous_step_start_and_end_index_and_resume_sheet3_info()
        json_list,first_round_json_list = self.__sys_file.read_previous_step_json_list_and_resume_sheet1_info(round_num, cur_index, end_index)    
        self.__move_previous_done_json_files_to_file_process_folder(json_list, first_round_json_list, round_num)
        self.__sys_file.resume_sheet2_info(round_num, end_index, len(json_list))    

# public
    def __init__(self, fm_process_que, td_que, shm_name, shm_size):
        self.__set_font.config(family='courier new', size=15)
        threading.Thread.__init__(self)
        self.fm_process_queue = fm_process_que
        self.td_queue = td_que
        self.pym = PYM.LOG(True)
        self.shm_id = shared_memory.ShareableList(name=shm_name)
        self.__interval = 1 
        self.__sys_file = None
        self.__cur_target_index = 0
        self.__this_round_end_index = 0
        self.pym.PY_LOG(False, 'D', self.__log_name, 'init finished')

    def __del__(self):
        #deconstructor
        self.shut_down_log("over")
        self.shm_id.shm.close()

    def FMP_main(self, msg):
        self.pym.PY_LOG(False, 'D', self.__log_name, 'receive msg from queue: ' + msg)
        if msg[:15] == "json_file_path:":
            self.__deal_with_json_file_path_command(msg)
        elif msg[:27] == 'check_file_exist_and_match:':
            self.__read_interval_from_msg(msg)
            # make sure file_process folder is existed
            if os.path.isdir(self.__file_process_path) != 0:
                if self.__deal_with_file_list():
                    self.__notify_tool_display_process_file_exist()
                    self.__deal_with_run_feature_match_command()
                    self.pym.PY_LOG(False, 'D', self.__log_name, '!!---FINISHED THIS ROUND,WAIT FOR NEXT ROUND---!!\n\n\n\n\n')
                else:
                    self.__notify_tool_display_process_file_too_few()
                    self.pym.PY_LOG(True, 'E', self.__log_name, 'json files too few!!')
            else:
                self.__notify_tool_display_process_file_not_exist()
                self.pym.PY_LOG(True, 'E', self.__log_name, 'There are no file_process folder!!')
                self.shut_down_log("over")
        elif msg == 'ask_prv_action:':
            self.pym.PY_LOG(False, 'D', self.__log_name, 'ask_prv_action')
            if self.__sys_file is None:
                self.pym.PY_LOG(False, 'D', self.__log_name, 'no create class sys_file')
                self.__sys_file =  SF.system_file(self.__file_path, "", "")
                self.pym.PY_LOG(False, 'D', self.__log_name, 'created class sys_file')
            
            if self.__sys_file.is_first_load_json() == True:
                self.pym.PY_LOG(False, 'D', self.__log_name, 'first load')
                self.td_queue.put('no_prv_step')
            else:
                self.pym.PY_LOG(False, 'D', self.__log_name, 'not first load')
                self.td_queue.put('has_prv_step')
        elif msg == 'run_prv_action:':  
            self.__run_resume_to_previous_state()
            self.td_queue.put('prv_finished:')



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
        if len(self.__ovij_list) != 0:
            for i in range(len(self.__ovij_list)):
                self.__ovij_list[i].shut_down_log("%d pym over" %i)  

        # delete cv_sift_match's pym process
        if self.__cvSIFTmatch is not None:
            self.__cvSIFTmatch.shut_down_log("over")

        # delete system_file process
        if self.__sys_file is not None:
            self.__sys_file.shut_down_log("over")

    def show_error_msg_on_toast(self, title, msg):
        messagebox.showerror(title, msg)

    def show_info_msg_on_toast(self, title, msg):
        messagebox.showinfo(title, msg)

