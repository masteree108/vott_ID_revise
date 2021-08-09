# this class for dealing with json(only read id and timestamp and fill into excel) and excel file
import os
import json
import log as PYM
import numpy as np
import pandas as pd 
from _pydecimal import Decimal, Context, ROUND_HALF_UP 
from openpyxl import load_workbook
import shutil

class system_file():
# private
    __log_name = '< class system_file>'
    __json_id = ''
    __json_timestamp_list = []
    __json_list = []
    __excel_save_path = './.system/system_config.xlsx'
    __excel_sheet1_name = 'seq_list'
    __excel_sheet2_name = 'config'
    __excel_sheet3_name = 'cal'
    __vott_set_fps = 6
    __first_timestamp_index = 0

    # unit: second ,DP=Decimal point
    __frame_timestamp_DP_15fps = [0, 0.066667, 0.133333, 0.2, 0.266667, 0.333333,
                       0.4, 0.466667, 0.533333, 0.6, 0.666667, 0.733333,
                       0.8, 0.866667, 0.933333]                                                                                                     

    __format_15fps = ['mp4', '066667', '133333', '2', '266667', '333333',
                       '4', '466667', '533333', '6', '666667', '733333',
                       '8', '866667', '933333']
        
    # if there is needing another format fps please adding here
        
    __frame_timestamp_DP_6fps = [0, 0.166667, 0.333333, 0.5, 0.666667, 0.833333]
    __format_6fps = ['mp4', '166667', '333333', '5', '666667', '833333']
        
    __frame_timestamp_DP_5fps = [0, 0.2, 0.4, 0.6, 0.8]
    __format_5fps = ['mp4', '2', '4', '6', '8']
        
    ''' 
        pick up frame description:
        if source_video_fps = 29,
        (1) setted project frame rate = 29, pick up 29 frames(1sec)
            pick_up_frame_interval = 1
            loop_counter(start number is 0)
            pick up frame:  | judgement:   
            0               | == 1-1 (pick_up_interval -1)
            1               | == 2-1 
            2               | == 3-1
            ...
            28              | == 29-1

       (2) setted project frame rate = 15, only pick 15 frames from 30 frames(1sec)
            pick_up_frame_interval = round(29/15) = 2
            loop_counter(start number is 0)
            pick up frame:  | judgement:   
            1               | == 2-1 (pick_up_interval -1)
            3               | == 4-1 
            5               | == 6-1
            7               | == 8-1
            9               | == 10-1
            11              | == 12-1
            13              | == 14-1
            15              | == 16-1
            17              | == 18-1
            19              | == 20-1
            21              | == 22-1
            23              | == 24-1
            25              | == 26-1
            27              | == 28-1
            29              | == 30-1
 
        (3) setted project frame rate = 6, only pick 6 frames from 30 frames(1 sec)
            pick_up_frame_interval = round(29/6) = 5
            loop_counter(start number is 0)
            pick up frame:  | judgement:   
            4               | == 5-1 (pick_up_interval -1)
            9               | == 10-1 
            14              | == 15-1
            19              | == 20-1
            24              | == 25-1
            29              | == 30-1

        (4) setted project frame rate = 5, only pick 5 frames from 30 frames(1 sec)
            pick_up_frame_interval = round(29/5) = 6
            loop_counter(start number is 0)
            pick up frame:  | judgement:   
            5               | == 6-1 (pick_up_interval -1)
            11              | == 12-1 
            17              | == 18-1
            23              | == 24-1
            29              | == 30-1
 
    '''

    def __read_id_and_timestamp_from_id_json_files(self, json_file_folder_path,  all_file_list):
        self.pym.PY_LOG(False, 'D', self.__log_name, '__read_data_from_json_file')
        ct = 0
        drop_flag = False
        id_val = ''
        timestamp = ''
        for i,file_path in enumerate(all_file_list):
            file_path = json_file_folder_path + '/' + file_path
            try:
                with open(file_path, 'r') as reader:
                    drop_flag = False
                    self.pym.PY_LOG(False, 'D', self.__log_name, '%s open ok!' % file_path)
                    jf = json.loads(reader.read())
                    self.__json_list.append([])
                    id_val = jf['asset']['id'] + '-asset.json'
                    self.__json_id = id_val
                    timestamp =  jf['asset']['timestamp']
            except:
                drop_flag = True
                os.remove(file_path)
                self.pym.PY_LOG(False, 'E', self.__log_name, '%s has wrong format(maybe json content only bascally framework data but no user data!' % self.__json_id)
            if drop_flag == False:
                self.__json_list[ct].append(id_val)
                self.__json_list[ct].append(timestamp)
                ct += 1
                self.__json_timestamp_list.append(timestamp)


    def __vott_set_fps_judgement(self, tsp1, tsp2):
        vott_set_fps = 1 / (tsp2 - tsp1)                                 
        vott_set_fps = round(vott_set_fps, 1)
        self.pym.PY_LOG(False, 'D', self.__log_name, 'vott_set_fps: %s' % str(vott_set_fps))
        return int(vott_set_fps)

    # if first json timestamp is not at frame1, we can use this function to check(only for first load json files)
    def __find_first_json_index(self, sort_timestamp):                                                                                                          
        first_timestamp = sort_timestamp[0]
        first_timestamp_sec = int(first_timestamp)
        diff = first_timestamp - first_timestamp_sec
        self.pym.PY_LOG(False, 'D', self.__log_name, 'first timestamp diff:%s' % diff)
        first_index = self.timestamp_index(self.__vott_set_fps, diff)
        self.pym.PY_LOG(False, 'D', self.__log_name, 'first timestamp index:%d' % first_index)
        return first_index

    def __every_sec_last_frame_timestamp(self, index):
        vott_set_fps = self.__vott_set_fps
        if vott_set_fps == 5:
            return self.__frame_timestamp_DP_5fps[4]
        elif vott_set_fps == 6:
            return self.__frame_timestamp_DP_6fps[5]
        elif vott_set_fps == 15:
            return self.__frame_timestamp_DP_15fps[14]

    def __excel_column_width_settings(self, writer):
        writer.sheets[self.__excel_sheet1_name].column_dimensions['A'].width = 20
        writer.sheets[self.__excel_sheet1_name].column_dimensions['B'].width = 50
        writer.sheets[self.__excel_sheet1_name].column_dimensions['C'].width = 10
        writer.sheets[self.__excel_sheet1_name].column_dimensions['D'].width = 20
        writer.sheets[self.__excel_sheet1_name].column_dimensions['E'].width = 20
            
        writer.sheets[self.__excel_sheet2_name].column_dimensions['A'].width = 20
        writer.sheets[self.__excel_sheet2_name].column_dimensions['B'].width = 20
        writer.sheets[self.__excel_sheet2_name].column_dimensions['C'].width = 30
        writer.sheets[self.__excel_sheet2_name].column_dimensions['D'].width = 30
        writer.sheets[self.__excel_sheet2_name].column_dimensions['E'].width = 30

        writer.sheets[self.__excel_sheet3_name].column_dimensions['A'].width = 20
        writer.sheets[self.__excel_sheet3_name].column_dimensions['B'].width = 20
        writer.sheets[self.__excel_sheet3_name].column_dimensions['C'].width = 20


# public
    def __init__(self, json_file_folder_path, all_file_list, state):
        # below(True) = exports log.txt
        self.pym = PYM.LOG(True)
        if state == "create_excel":
            self.__read_id_and_timestamp_from_id_json_files(json_file_folder_path, all_file_list)
        self.pym.PY_LOG(False, 'D', self.__log_name, 'init finished')

    def __del__(self):
        #deconstructor
        self.shut_down_log("over")

    def id_and_timestamp_fill_into_excel(self):
        if len(self.__json_timestamp_list) > 0:
            timestamp_with_sort = []
            timestamp_with_sort = self.__json_timestamp_list.copy()

            self.pym.PY_LOG(False, 'D', self.__log_name, 'start sort')
            #sort timestamp
            timestamp_with_sort.sort()
            self.pym.PY_LOG(False, 'D', self.__log_name, 'sort ok')
            
            #sort self.__json_list depends on temp
            find_index = np.array(self.__json_timestamp_list)
            sort_json_list_temp = []
            for i,tps in enumerate(timestamp_with_sort):
                index = np.argwhere(find_index == tps)
                sort_json_list_temp.append(self.__json_list[int(index)])
           
            self.__vott_set_fps = self.__vott_set_fps_judgement(timestamp_with_sort[0], timestamp_with_sort[1])

            self.__first_timestamp_index = self.__find_first_json_index(timestamp_with_sort)

            # clear json_list
            self.__json_list = []
            self.__json_list = sort_json_list_temp.copy()

            amount_of_json = len(self.__json_list)

            # save sort list to excel
            asset_id_list = []
            timestamp_list = []
            changed_list = []
            compare_state_list = []
            record_index_list = []
            
            for i,info in enumerate(self.__json_list):
                #self.pym.PY_LOG(False, 'D', self.__log_name, '%s' % info[0])
                #self.pym.PY_LOG(False, 'D', self.__log_name, '%s' % info[1])
                asset_id_list.append(info[0])
                timestamp_list.append(info[1])
                changed_list.append('N')
                compare_state_list.append('')
                if i == 0:
                    record_index_list.append('here')
                else:
                    record_index_list.append('')

            writer = pd.ExcelWriter(self.__excel_save_path)
            excel_sheet1 = pd.DataFrame({'timestamp':timestamp_list, 'asset_id':asset_id_list, 'changed':changed_list, \
                                'compare_state': compare_state_list, 'record_index':record_index_list})
            excel_sheet1.to_excel(writer, index=False, sheet_name=self.__excel_sheet1_name)
            
            save_fps_list = []
            save_fps_list.append(self.__vott_set_fps)
            amount_of_json_list = []
            amount_of_json_list.append(amount_of_json)
            done_json_list = []
            done_json_list.append(0)
            done_json_index_list =[]
            done_json_index_list.append(0)
            first_load_list = []
            first_load_list.append('Y')
            excel_sheet2 = pd.DataFrame({'vott_set_fps':save_fps_list, 'amount_of_json':amount_of_json_list, \
                                        'amount_of_done_json':done_json_list, 'done_json_index':done_json_index_list, 'first_load':first_load_list});
            excel_sheet2.to_excel(writer, index=False, sheet_name=self.__excel_sheet2_name)


            round_number_list = []
            round_interval_list = []
            cur_index_list = []
            round_number_list.append(0)
            cur_index_list.append(0)
            round_interval_list.append(0)
            excel_sheet3 = pd.DataFrame({'round_number':round_number_list,'round_interval':round_interval_list, 'cur_index':cur_index_list});
            excel_sheet3.to_excel(writer, index=False, sheet_name=self.__excel_sheet3_name)
            
            self.__excel_column_width_settings(writer)
            writer.save()
            del self.__json_list
            self.__json_timestamp_list = []
            return True
        else:
            self.pym.PY_LOG(False, 'E', self.__log_name, 'there are no any json files')
            return False

    def shut_down_log(self, msg):
        self.pym.PY_LOG(True, 'D', self.__log_name, msg)

    def read_vott_set_fps(self):
        tag_name = 'vott_set_fps'
        df = pd.read_excel(self.__excel_save_path, sheet_name = self.__excel_sheet2_name, usecols=[tag_name])
        self.__vott_set_fps = df[tag_name][0]
        self.pym.PY_LOG(False, 'D', self.__log_name, 'read_vott_set_fps:%d' % self.__vott_set_fps)
        return self.__vott_set_fps


    def timestamp_index(self, vott_set_fps, diff):
        val = Decimal(diff).quantize(Decimal('0.00'))
        self.pym.PY_LOG(False, 'D', self.__class__, 'val:%s' % str(val))                                                                                        
        fps = []          
        if vott_set_fps == 5:
            for i in self.__frame_timestamp_DP_5fps:
                temp = Decimal(i).quantize(Decimal('0.00'))
                fps.append(temp)
        elif vott_set_fps == 6:
            for i in self.__frame_timestamp_DP_6fps:
                temp = Decimal(i).quantize(Decimal('0.00'))
                fps.append(temp)
        elif vott_set_fps == 15:
            for i in self.__frame_timestamp_DP_15fps:
                tmep = Decimal(i).quantize(Decimal('0.00'))
                fps.append(temp) 
        else:
            for i in vott_set_fps:
                fps.append(i)
        fps_array = np.array(fps)
        index = np.argwhere(fps_array == val)
        self.pym.PY_LOG(False, 'D', self.__class__, 'index:%s' % str(index))
                          
        return int(index)

    def read_left_amount_of_json(self):
        # read done json from excel system_config
        tag_name1 = 'amount_of_json'
        tag_name2 = 'amount_of_done_json'
        self.pym.PY_LOG(False, 'D', self.__log_name, 'read_left_amount_of_json')
        df = pd.read_excel(self.__excel_save_path, sheet_name = self.__excel_sheet2_name, usecols=[tag_name1, tag_name2])
        amount_of_json = df[tag_name1][0]
        amount_of_done_json = df[tag_name2][0]
        left_json = amount_of_json - amount_of_done_json + 1
        self.pym.PY_LOG(False, 'D', self.__log_name, 'left_amount_of_json:%d' % left_json)
        return int(left_json)


    def is_first_load_json(self):
        tag_name = 'first_load'
        df_sheet2 = pd.read_excel(self.__excel_save_path, sheet_name = self.__excel_sheet2_name, usecols=[tag_name])
        state = str(df_sheet2[tag_name][0])
        self.pym.PY_LOG(False, 'D', self.__log_name, 'first load state:%s' % state)
        if state == 'Y':
            return True
        else:
            return False

    def read_first_timestamp_index(self):
        return self.__first_timestamp_index

    def read_previous_round_done_index(self):
        tag_name = 'done_json_index'
        df_sheet2 = pd.read_excel(self.__excel_save_path, sheet_name = self.__excel_sheet2_name, usecols=[tag_name])
        previous_done_index = df_sheet2[tag_name] 
        return int(previous_done_index)

    def read_this_round_json_list(self, cur_target_index, this_round_end_index):
        json_list = []
        tag_name = 'asset_id'
        # read json list from excel system_config
        self.pym.PY_LOG(False, 'D', self.__log_name, 'read_this_round_json_list')
        df_sheet1 = pd.read_excel(self.__excel_save_path, sheet_name = self.__excel_sheet1_name, usecols=[tag_name])
        
        for i in range(cur_target_index, this_round_end_index + 1):
            json_list.append(df_sheet1[tag_name][i]) 
            self.pym.PY_LOG(False, 'D', self.__log_name, 'this round json asset_id:%s' % df_sheet1[tag_name][i])
        return json_list

    def check_calibrate_index_and_get_cur_frame_target_index(self, cal_amount_of_json):
        timestamp_list = []
        tag_name = 'timestamp'
        # load json list from excel
        self.pym.PY_LOG(False, 'D', self.__log_name, 'check_index_is_correct_and_calculate_cur_target')
        df_sheet1 = pd.read_excel(self.__excel_save_path, sheet_name = self.__excel_sheet1_name, usecols=[tag_name])

        previous_done_index = self.read_previous_round_done_index()
        end_index = previous_done_index + cal_amount_of_json - 1
        self.pym.PY_LOG(False, 'D', self.__log_name, 'cal_amount_of_json:%d' % cal_amount_of_json)
        self.pym.PY_LOG(False, 'D', self.__log_name, 'end_index:%d' % end_index)
        
        for i in range(previous_done_index, end_index+1):
            self.pym.PY_LOG(False, 'D', self.__log_name, 'sheet1[%d]' % i)
            self.pym.PY_LOG(False, 'D', self.__log_name, '%s' % str(df_sheet1[tag_name][i]))
            timestamp_list.append(df_sheet1[tag_name][i])
            
        cur_target_index = previous_done_index + int(cal_amount_of_json / 2) 

        # before index checking and calibrating
        if self.is_first_load_json() == True:
            self.pym.PY_LOG(False, 'D', self.__log_name, 'first_load_json,fps:%d' % self.__vott_set_fps)
            cur_target_index = previous_done_index + int(cal_amount_of_json / 2) 
            self.pym.PY_LOG(False, 'D', self.__log_name, '(first load) cur_target_index:%d' % cur_target_index)
            last_index_val = self.__every_sec_last_frame_timestamp(cur_target_index)
            u_index = cur_target_index
            d_index = cur_target_index
            # check and calibrate current target index
            for i in range(self.__vott_set_fps):
                u_timestamp = int((timestamp_list[u_index])*1000 - int(timestamp_list[u_index])*1000)
                self.pym.PY_LOG(False, 'D', self.__log_name, 'u_timestamp:%d' % u_timestamp)

                d_timestamp = (timestamp_list[d_index])*1000 - int(timestamp_list[d_index])*1000
                #self.pym.PY_LOG(False, 'D', self.__log_name, 'd_timestamp:%s' % str(d_timestamp))
                if u_timestamp == int(last_index_val*1000):
                    self.pym.PY_LOG(False, 'D', self.__log_name, 'calibrated cur_target_index:%s is corret' % str(u_index))
                    cur_target_index = u_index
                    break
                elif d_timestamp == int(last_index_val*1000):
                    self.pym.PY_LOG(False, 'D', self.__log_name, 'calibrated cur_target_index:%s is corret' % str(d_index))
                    cur_target_index = d_index
                    break
                else:
                    # look back at timestamp list
                    u_index -= 1
                    # look after at timestamp list
                    d_index += 1

            # check and calibrate this round end index
            u_index = end_index
            self.pym.PY_LOG(False, 'D', self.__log_name, 'len(timestamp_list):%d' % len(timestamp_list))
            for i in range(self.__vott_set_fps):
                u_timestamp = int((timestamp_list[u_index])*1000 - int(timestamp_list[u_index])*1000)
                self.pym.PY_LOG(False, 'D', self.__log_name, 'u_timestamp:%d' % u_timestamp)

                if u_timestamp == int(last_index_val*1000) :
                    self.pym.PY_LOG(False, 'D', self.__log_name, 'calibrated this round end_index:%s is corret' % str(u_index))
                    end_index = u_index
                    break
                else:
                    # look back at timestamp list
                    u_index -= 1

        else:
            self.pym.PY_LOG(False, 'D', self.__log_name, 'not first_load_json,fps:%d' % self.__vott_set_fps)
            cur_target_index = previous_done_index
            '''
            last_index_val = self.__every_sec_last_frame_timestamp(cur_target_index)

            # check and calibrate this round end index
            u_index = len(timestamp_list) - 1
            self.pym.PY_LOG(False, 'D', self.__log_name, 'len(timestamp_list):%d' % len(timestamp_list))
            for i in range(self.__vott_set_fps):
                u_timestamp = int((timestamp_list[u_index])*1000 - int(timestamp_list[u_index])*1000)
                self.pym.PY_LOG(False, 'D', self.__log_name, 'u_timestamp:%s' % str(u_timestamp))
                if u_timestamp == int(last_index_val*1000):
                    self.pym.PY_LOG(False, 'D', self.__log_name, 'calibrated (not first load)this round end_index:%s is corret' % str(u_index))
                    end_index = u_index
                    break
                else:
                    # look back at timestamp list
                    u_index -= 1
            '''
        return cur_target_index, end_index


    def update_excel_sheet1(self, cur_target_index, this_round_end_index):
        tag_name3 = 'changed'
        tag_name4 = 'compare_state'
        tag_name5 = 'record_index'
        
        #first_load_flag = 'N'
        #if self.is_first_load_json() == True:
            #first_load_flag = 'Y'

        previous_round_done_index = self.read_previous_round_done_index() 
        df_sheet1 = pd.read_excel(self.__excel_save_path, sheet_name = self.__excel_sheet1_name)
        df_sheet2 = pd.read_excel(self.__excel_save_path, sheet_name = self.__excel_sheet2_name)
        df_sheet3 = pd.read_excel(self.__excel_save_path, sheet_name = self.__excel_sheet3_name)

        next_index = cur_target_index + 1
        for i in range(next_index, this_round_end_index+1):
            df_sheet1[tag_name3][i] = 'Y'

        #if first_load_flag == 'Y':
        df_sheet1[tag_name4][cur_target_index] = 'cur_compare'
        df_sheet1[tag_name4][cur_target_index+1] = 'next_compare'
        #else:
           # df_sheet1[tag_name4][this_round_end_index-1] = 'cur_compare'
           # df_sheet1[tag_name4][this_round_end_index] = 'next_compare'

        df_sheet1[tag_name5][previous_round_done_index] = ''
        df_sheet1[tag_name5][this_round_end_index] = 'here'

        writer = pd.ExcelWriter(self.__excel_save_path)
        df_sheet1.to_excel(writer, sheet_name=self.__excel_sheet1_name, index=False)
        df_sheet2.to_excel(writer, sheet_name=self.__excel_sheet2_name , index=False)
        df_sheet3.to_excel(writer, sheet_name=self.__excel_sheet3_name , index=False)

        self.__excel_column_width_settings(writer)
        writer.save()

    def update_excel_sheet2(self, cur_index, done_json_index, first_load):
        tag_name3 = 'amount_of_done_json'
        tag_name4 = 'done_json_index'
        tag_name5 = 'first_load'
        df_sheet1 = pd.read_excel(self.__excel_save_path, sheet_name = self.__excel_sheet1_name)
        df_sheet2 = pd.read_excel(self.__excel_save_path, sheet_name = self.__excel_sheet2_name)
        df_sheet3 = pd.read_excel(self.__excel_save_path, sheet_name = self.__excel_sheet3_name)
        df_sheet2[tag_name3][0] = done_json_index + 1
        df_sheet2[tag_name4][0] = done_json_index
        df_sheet2[tag_name5][0] = first_load

        writer = pd.ExcelWriter(self.__excel_save_path)
        df_sheet1.to_excel(writer, sheet_name=self.__excel_sheet1_name, index=False)
        df_sheet2.to_excel(writer, sheet_name=self.__excel_sheet2_name , index=False)
        df_sheet3.to_excel(writer, sheet_name=self.__excel_sheet3_name , index=False)

        self.__excel_column_width_settings(writer)
        writer.save()

    def update_excel_sheet3(self, round_interval, cur_index):
        first_load_state = 'N'
        if self.is_first_load_json() == True:
            first_load_state = 'Y'

        # first round number column length
        tag_name1 = 'round_number'
        tag_name2 = 'round_interval'
        tag_name3 = 'cur_index'
        df_sheet1 = pd.read_excel(self.__excel_save_path, sheet_name = self.__excel_sheet1_name)
        df_sheet2 = pd.read_excel(self.__excel_save_path, sheet_name = self.__excel_sheet2_name)
        df_sheet3 = pd.read_excel(self.__excel_save_path, sheet_name = self.__excel_sheet3_name)

        update_index = len(df_sheet3[tag_name1])
        self.pym.PY_LOG(False, 'D', self.__log_name, 'update_excel_sheet3, update_index:%d' % update_index)

        new_sheet3 = pd.DataFrame()
        if first_load_state == 'Y':
            df_sheet3[tag_name1][0] = update_index
            df_sheet3[tag_name2][0] = round_interval
            df_sheet3[tag_name3][0] = cur_index
        else:
            round_number_list = []
            round_number_list.append(update_index+1)
            round_interval_list = []
            round_interval_list.append(round_interval)
            cur_index_list = []
            cur_index_list.append(cur_index)
            new_row = pd.DataFrame({tag_name1: round_number_list, tag_name2:round_interval_list, tag_name3:cur_index_list})
            new_sheet3 = pd.concat([df_sheet3,new_row], ignore_index = True, axis = 0)

        writer = pd.ExcelWriter(self.__excel_save_path)
        df_sheet1.to_excel(writer, sheet_name=self.__excel_sheet1_name, index=False)
        df_sheet2.to_excel(writer, sheet_name=self.__excel_sheet2_name , index=False)
        if first_load_state == 'Y':
            df_sheet3.to_excel(writer, sheet_name=self.__excel_sheet3_name , index=False)
        else:
            new_sheet3.to_excel(writer, sheet_name=self.__excel_sheet3_name , index=False)
        self.__excel_column_width_settings(writer)
        writer.save()
        
    def get_this_round_move_list(self, this_round_done_json_index):
        this_round_move_list = []
        # read previous round done json index
        tag_name = 'done_json_index'
        asset_id = ''
        df_sheet1 = pd.read_excel(self.__excel_save_path, sheet_name = self.__excel_sheet1_name)
        df_sheet2 = pd.read_excel(self.__excel_save_path, sheet_name = self.__excel_sheet2_name)
        previous_round_done_json_index = df_sheet2[tag_name][0]
        #not include this round last asset-id json file
        for i in range(previous_round_done_json_index, this_round_done_json_index+1):
            asset_id = df_sheet1['asset_id'][i]
            this_round_move_list.append(asset_id)
            self.pym.PY_LOG(False, 'D', self.__log_name, 'this round move json asset_id:%s ' % asset_id)
            
        return this_round_move_list

    def copy_excel_to_result_folder(self, des_path):
        shutil.copyfile(self.__excel_save_path, des_path)

