import threading
import queue
#import numpy as np
import easygui as GUI
import SharedArray as sa

class gui_dialog(threading.Thread):
# private
    __log_name = '< class feature_match_process>'
    __share_array_name = 'new_id'

    # public
    def __init__(self, dialog_queue):
        threading.Thread.__init__(self)
        self.dialog_queue = dialog_queue
        # delete share array if this process close method is not right
        for name in sa.list():
            shm_name = name.name.decode('utf-8')
            sa.delete(shm_name)

        self.shm_id = sa.create("shm://" + self.__share_array_name, 10)

    def __del__(self):
        #deconstructor
        del self.shm_id
        try:
            sa.delete(self.__share_array_name)
        except:
            print("del shm_id")
            #self.pym.PY_LOG(False, 'D', self.__log_name, 'share_array:%s has been deleted' % self.__share_array_name)
        #self.shut_down_log("over")

    def run(self):
        #self.pym.PY_LOG(False, 'D', self.__log_name, 'run')
        while True:
            msg = self.dialog_queue.get()
            try:
                if msg == 'dialog':
                    result = GUI.integerbox(msg='請比對id table並輸入id號碼',title ='無法辨識此人', default=1)
                    self.shm_id[0] = float(result)
                    #print("type: %d" % result)
                elif msg == 'over':
                    break
            except:
                del self.shm_id
                print("error") 

        #self.shut_down_log("fm_rpocess_over")
    '''
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
    '''
    
