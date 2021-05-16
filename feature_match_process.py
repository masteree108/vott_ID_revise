import os
import sys
import json
import enum
import threading
import queue
import numpy as np
import shutil

import read_vott_id_json as RVIJ
import log as PYM

# command from tool_display process:
# json_file_path:
# (1) copy data to ./data_process folder
# (2) load data into every rvij class
# (3) sort rvij_list
# save status_json

class BBOX_ITEM(enum.Enum):
    height = 0
    width = 1
    left = 2
    top = 3

class VIDEO_SIZE(enum.Enum):
    W = 0
    H = 1

class feature_match_process(threading.Thread):
# private
    __log_name = '< class feature_match_process>'
    __rvij_list = []
    __all_json_file_list = []
    __rvij_list_with_sort = []
    __amount_of_rvij = 0
    __file_process_path = './file_process/' 
    __file_path = ''

    def __copy_all_json_file(self):
        if os.path.isdir(self.__file_process_path) == 0:
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
            self.__all_json_file_list = temp
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
            

    def __create_rvij_list(self):
        self.pym.PY_LOG(False, 'D', self.__log_name, 'amount of data: %s' % str(self.__amount_of_rvij))
        for i in range(self.__amount_of_rvij):
            self.__rvij_list.append(RVIJ.read_vott_id_json())

    def __sort_rvij_list(self):
        temp_no_sort = []
        for i in range(self.__amount_of_rvij):
            temp_no_sort.append(self.__rvij_list[i].get_timestamp())
            self.pym.PY_LOG(False, 'D', self.__log_name, 'timestamp without sort %s' % str(temp_no_sort[i]))
        temp_sort = temp_no_sort.copy()
        temp_sort.sort() 
        #for i in range(self.__amount_of_rvij):
            #self.pym.PY_LOG(False, 'D', self.__log_name, 'timestamp with sort %s' % str(temp_sort[i]))

        find_index = np.array(temp_no_sort)
        # sort rvij_list-method0
        for i, tps in enumerate(temp_sort):
            index = np.argwhere(find_index == tps)
            self.__rvij_list_with_sort.append(self.__rvij_list[int(index)])
        '''
        # sort rvij_list-method1 equal above sort rvij_list-method0
        for i, tps in enumerate(temp_sort):
            for j, tpns in enumerate(temp_no_sort):
                if tps == tpns:
                    print("tps:%s"% str(tps)+' '+str(i))
                    print("tpns:%s"% str(tpns)+' '+str(j))
                    self.__rvij_list_with_sort.append(self.__rvij_list[j])
                    break
        '''
        for i in range(self.__amount_of_rvij):
            self.pym.PY_LOG(False, 'D', self.__log_name, 'rvij_list with sort %s' % str(self.__rvij_list_with_sort[i].get_timestamp()))


# public
    def __init__(self, fm_process_que, td_que):
        threading.Thread.__init__(self)
        self.fm_process_queue = fm_process_que
        self.td_queue = td_que
        self.pym = PYM.LOG(True)
        self.pym.PY_LOG(False, 'D', self.__log_name, 'init')
        
    def FMP_main(self, msg):
        self.pym.PY_LOG(False, 'D', self.__log_name, 'receive msg from queue: ' + msg)
        if msg[:15] == "json_file_path:":
            self.__file_path = msg[15:]
            if self.__list_all_json_file(self.__file_path) == 0:
                #copy all of json data to ./process data folder
                self.__copy_all_json_file()

                # creates rvij_lsit[]
                self.__amount_of_rvij = len(self.__all_json_file_list)
                self.__create_rvij_list()

                # read json data and fill into rvij_list[num]
                for i in range(self.__amount_of_rvij):
                    self.__rvij_list[i].read_all_data_info(self.__file_process_path, self.__all_json_file_list[i])

                # sort rvij_list by timestamp
                self. __sort_rvij_list()


            else:
                self.pym.PY_LOG(True, 'E', self.__log_name, 'There are no any *.json data')
                self.shut_down_log("over")
            

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

        # delete all rvij_list's pym process
        amt_rvij_list = len(self.__rvij_list)
        if amt_rvij_list != 0:
            for i in range(amt_rvij_list):
                self.__rvij_list[i].shut_down_log("%d pym over" %i)  
    

