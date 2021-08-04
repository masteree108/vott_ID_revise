# this class for dealing with json(only read id and timestamp and fill into excel) and excel file
import os
import json
import log as PYM
import numpy as np
import pandas as pd 

class system_file():
# private
    __log_name = '< class system_file>'
    __json_id = ''
    __json_timestamp_list = []
    __json_list = []
    __json_file_folder_path = ''
    __excel_save_path = './.system/system_config.xlsx'
    __excel_sheet1_name = 'seq_list'
    __excel_sheet2_name = 'config'
    __vott_set_fps = 6

    def __read_id_and_timestamp_from_id_json_files(self, json_file_folder_path,  all_file_list):
        self.pym.PY_LOG(False, 'D', self.__log_name, '__read_data_from_json_file')
        ct = 0
        for i,file_path in enumerate(all_file_list):
            file_path = json_file_folder_path + '/' + file_path
            self.pym.PY_LOG(False, 'D', self.__log_name, '%s open ok!' % file_path)
            try:
                with open(file_path, 'r') as reader:
                    self.pym.PY_LOG(False, 'D', self.__log_name, '%s open ok!' % file_path)
                    jf = json.loads(reader.read())
                    self.__json_list.append([])
                    id_val = jf['asset']['id'] + '-asset.json'
                    self.__json_id = id_val
                    self.__json_list[ct].append(id_val)
                    self.__json_list[ct].append(jf['asset']['timestamp'])
                    ct += 1
                    self.__json_timestamp_list.append(jf['asset']['timestamp'])
            except:
                self.pym.PY_LOG(False, 'E', self.__log_name, '%s has wrong format!' % self.__json_id)


    def __vott_set_fps_judgement(self, tsp1, tsp2):
        vott_set_fps = 1 / (tsp2 - tsp1)                                 
        vott_set_fps = round(vott_set_fps, 1)
        self.pym.PY_LOG(False, 'D', self.__log_name, 'vott_set_fps: %s' % str(vott_set_fps))
        return vott_set_fps


# public
    def __init__(self, json_file_folder_path, all_file_list):
        # below(True) = exports log.txt
        self.pym = PYM.LOG(True)
        self.__json_file_folder_path = ''
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

            # clear json_list
            self.__json_list = []
            self.__json_list = sort_json_list_temp.copy()

            # save sort list to excel
            asset_id_list = []
            timestamp_list = []
            for i,info in enumerate(self.__json_list):
                #self.pym.PY_LOG(False, 'D', self.__log_name, '%s' % info[0])
                #self.pym.PY_LOG(False, 'D', self.__log_name, '%s' % info[1])
                asset_id_list.append(info[0])
                timestamp_list.append(info[1])

            writer = pd.ExcelWriter(self.__excel_save_path)
            excel_sheet1 = pd.DataFrame({'timestamp':timestamp_list, 'asset_id':asset_id_list});
            excel_sheet1.to_excel(writer, index=False, sheet_name=self.__excel_sheet1_name)
            writer.sheets[self.__excel_sheet1_name].column_dimensions['A'].width = 20
            writer.sheets[self.__excel_sheet1_name].column_dimensions['B'].width = 50
            
            for_save_fps = []
            for_save_fps.append(self.__vott_set_fps)
            excel_sheet2 = pd.DataFrame({'fps':for_save_fps});
            excel_sheet2.to_excel(writer, index=False, sheet_name=self.__excel_sheet2_name)
            writer.sheets[self.__excel_sheet2_name].column_dimensions['A'].width = 10

            writer.save()
            del self.__json_list
            self.__json_timestamp_list = []
            return True
        else:
            self.pym.PY_LOG(False, 'E', self.__log_name, 'there are no any json files')
            return False

    def load_json_list_from_system_config(self):
        self.pym.PY_LOG(False, 'D', self.__log_name, 'load_json_file_list_from_system_config')
        if os.path.isfile(self.__excel_save_path):
            df = pd.read_excel(self.__excel_save_path, sheet_name = None, usecols=['asset_id'])
            print(df)
            return True
        else:
            self.pym.PY_LOG(False, 'E', self.__log_name, 'system_config.xlsx is not existed!!')
            return False

    def shut_down_log(self, msg):
        self.pym.PY_LOG(True, 'D', self.__log_name, msg)

    def read_vott_set_fps(self):
        return self.__vott_set_fps
