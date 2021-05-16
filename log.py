import os
import time
import threading
import queue
from datetime import datetime
import platform

class Worker(threading.Thread):
    def __init__(self, queue, num, lock, log_path):
        #print("worker __init__")
        threading.Thread.__init__(self)
        self.queue = queue
        self.num = num
        self.lock = lock
        self.log_path = log_path

    def write_log_into_file(self, msg):
        with open(self.log_path, 'a') as f:
            f.write(msg + '\n')
        f.close()

    def run(self):
        #print("Worker __run__")
        while True:
        #while self.queue.qsize() > 0:
            # get msf from queue
            msg = self.queue.get()
            #print("log Worker %d: %s" % (self.num, msg))
            self.lock.acquire()
            self.write_log_into_file(msg)
            self.lock.release()
            # exit log saving
            if msg[:6] == '__SD__':
                break
            #time.sleep(1)
        
class LOG():

#public
    def __init__(self, export):
        self.level = ['E', 'W', 'D']
        self.export = export
        self.log_dir = './NTUT/log/'
        self.log_name = 'log.txt'
        self.log_path = self.log_dir + self.log_name

        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
            if not os.path.isfile(self.log_path):
                os_name = self.which_os()
                print("OS: %s" % os_name)
                if os_name == 'Linux':
                    os.mknod(self.log_name)
                else:
                    self.create_file() 
        
        self.log_path = self.log_dir + self.log_name
        self.lock = threading.Lock()
        self.log_queue = queue.Queue()
        self.log_worker1 = Worker(self.log_queue, 1, self.lock, self.log_path)
        self.log_worker1.start()
    
    #def __del__(self):
        #print("LOG __del__")
        #self.log_worker1.join()

    def which_os(self):
        os_name = platform.system() 
        #if os_name == 'Linux':
        #elif os_name == 'Windows': 
        return os_name

    def create_file(self):
        f = open(self.log_path, 'w+')
        f.close()
        
    def PY_LOG(self, exit_log, level, py_name, message):
        
        self.message_combine = ""
        if level ==  self.level[0]:         
            self.message_combine = "(error): " + str(py_name) + " " + str(message)
        elif level == self.level[1]:       
            self.message_combine = "(warning): " + str(py_name) + " "  + str(message)
        elif level == self.level[2]:       
            self.message_combine = "(debug): " + str(py_name) + " " + str(message)
        print(self.message_combine)        

        if self.export:
            now = datetime.now()
            if exit_log:
                # shutdown saving log
                self.log_queue.put( "__SD__" + str(now) + " , " + str(self.message_combine))
                self.log_worker1.join()
            else:
                self.log_queue.put(str(now) + " , " + str(self.message_combine))
                
            #print(str(now) + " , " + self.message_combine)

