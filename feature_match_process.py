import os
import sys
import json
import enum
import log as PYM
import threading
import queue

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

    
# public
    def __init__(self, fm_process_que, td_que):
        threading.Thread.__init__(self)
        self.fm_process_queue = fm_process_que
        self.td_queue = td_que
        self.pym = PYM.LOG(True)
        self.pym.PY_LOG(False, 'D', self.__log_name, 'init')

    def run(self):
        self.pym.PY_LOG(False, 'D', self.__log_name, 'run')
        while True:
            msg = self.fm_process_queue.get() 
            self.pym.PY_LOG(False, 'D', self.__log_name, 'receive msg from queue: ' + msg)
            if msg == 'over':
                break
        self.shut_down_log("fm_rpocess_over")

    def shut_down_log(self, msg):
        self.pym.PY_LOG(True, 'D', self.__log_name, msg)

    

