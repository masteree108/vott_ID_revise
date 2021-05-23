import cv2
import sys
import os
import tkinter as Tk
import tkinter.font as font
from tkinter import messagebox
import matplotlib
import matplotlib.pyplot as plt
from PIL import Image, ImageTk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk as NavigationToolbar2TkAgg
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure
from tkinter import filedialog       #獲取文件全路徑
import log as PYM
import SharedArray as sa
import numpy as np 
import cv2

class tool_display():

#private
    __log_name = '< class tool display>'
    __root = Tk.Tk()
    __open_img_path = ''
    __canvas = 0
    __json_data_path = ''
    __file_process_path = './file_process/'
    __set_font = font.Font(name='TkCaptionFont', exists=True)
    __share_array_name = 'image'

    def __init_buttons(self):
        # quit button
        quit_btn = Tk.Button(master = self.__root, text = 'Quit', command = self._quit)
        quit_btn['font'] = self.__set_font
        #quit_btn.pack(side = Tk.BOTTOM)
        quit_btn.pack(side = Tk.RIGHT)
        
        # open image button, this is for testing function
        open_img_btn = Tk.Button(master = self.__root, text='選擇1張圖片', command = self.open_image)  #設置按鈕，並給它openpicture命令
        open_img_btn['font'] = self.__set_font
        open_img_btn.pack(side = Tk.RIGHT)
        
        # get *.json data path button
        # 設置按鈕，並給它openpicture命令
        get_json_data_path_btn = Tk.Button(master = self.__root, text='選擇json檔案來源資料夾', command = self.find_json_file_path)
        get_json_data_path_btn['font'] = self.__set_font
        get_json_data_path_btn.pack(side = Tk.RIGHT)
        
        # run button
        run_btn = Tk.Button(master = self.__root, text='run', command = self.run_feature_match)  #設置按鈕，並給它run命令
        run_btn['font'] = self.__set_font
        run_btn.pack(side = Tk.RIGHT)

        '''
        # delete share array if this process close method is not right
        for name in sa.list():
            shm_name = name.name.decode('utf-8')
            sa.delete(shm_name)
        '''

    def __check_file_not_finished(self):
        if os.path.isdir(self.__file_process_path) != 0:
            return self.askokcancel_msg_on_toast("注意", "還有尚未完成的檔案,是否要重新開始？")
        else:
            return True
#public
    def __init__(self, td_que, fm_process_que):
        self.__set_font.config(family='courier new', size=15)
        self.td_queue = td_que
        self.fm_process_queue = fm_process_que
        self.pym = PYM.LOG(True)
        matplotlib.use('TkAgg')

        #規定窗口大小
        self.__root.geometry('2000x2000')
        #self.__root.resizable(width = False, height = False)   # 固定长宽不可拉伸
        self.__root.title("統一VoTT json 檔案內的人物ID")
        self.figure, self.ax = plt.subplots(1, 1, figsize=(16, 8))
        image1 = cv2.imread("default_img/logo_combine.jpg")
        self.ax.imshow(image1)

        #放置標籤
        self.label = Tk.Label(self.__root,text = 'pictures will show in this place', image = None)   #創建一個標籤
        self.label.pack()

        #把繪製的圖形顯示到tkinter視窗上
        self.canvas_draw()

        #把matplotlib繪製圖形的導航工具欄顯示到tkinter視窗上
        toolbar = NavigationToolbar2TkAgg(self.__canvas, self.__root)
        toolbar.update()
        self.__canvas._tkcanvas.pack(side = Tk.TOP, fill = Tk.BOTH, expand = 1)

        self.__init_buttons()

    def __del__(self):               
        #deconstructor
        self.shut_down_log("over")
        '''
        try:
            sa.delete(self.__share_array_name)
        except:
            self.pym.PY_LOG(False, 'D', self.__log_name, 'share_array:%s has been deleted' % self.__share_array_name)
        '''

    def canvas_draw(self):
        self.__canvas = FigureCanvasTkAgg(self.figure, master = self.__root)
        self.__canvas.draw()
        self.__canvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand = 1)
        #return canvas

    def open_image(self):
        file_name = filedialog.askopenfilename()     #獲取文件全路徑
        self.__open_image_path = file_name
        if os.path.isfile(file_name):
            self.pym.PY_LOG(False, 'D', self.__log_name, 'open image path:' + '%s' % file_name)
            self.label.config(text = 'image path:' + file_name )  
            image = cv2.imread(file_name)
            self.ax.imshow(image)
        else:
            self.label.config(text = 'image path is not existed!!' )  

    def find_json_file_path(self):
        if self.__check_file_not_finished() == True:
            #start or restart this process
            file_path = filedialog.askdirectory()     #獲取*.json檔案資料夾路徑
            if os.path.isdir(file_path):
                self.pym.PY_LOG(False, 'D', self.__log_name, 'json file path:' + '%s' % file_path)
                self.fm_process_queue.put("json_file_path:" + str(file_path)); 
                self.label.config(text = 'json file path:' + file_path )  
            else:
                self.pym.PY_LOG(False, 'D', self.__log_name, 'json file path:' + '%s' % file_path + 'is not existed!!')
                self.label.config(text = 'json file path is not existed!!' )  
        else:
            self.show_info_msg_on_toast("提醒", "請繼續執行 run 按鈕")
            

    def run_feature_match(self):
        self.pym.PY_LOG(False, 'D', self.__log_name, 'run_feature_match')
        self.fm_process_queue.put("run_feature_match") 
        
        msg = self.td_queue.get()
        if msg[:23]== 'show_cur_ids_img_table:':
            with open('cur_ids_img_table', 'rb') as f:
                str_encode = f.read()
            decode_img = np.asarray(bytearray(str_encode), dtype='uint8')
            decode_img = cv2.imdecode(decode_img, cv2.IMREAD_COLOR)
            cv2.imwrite('fff.png', decode_img)
            
            # below is using share array but failed
            #b = sa.attach("shm://" + self.__share_array_name)
            #decode_img = np.asarray(bytearray(c), dtype='uint8')
            #decode_img = cv2.imdecode(decode_img, cv2.IMREAD_COLOR)
            #self.fm_process_queue.put('delete_a')
            #cv2.imwrite('fff.png', decode_img)
            #cv2.waitKey(0)
            #cv2.destroyAllWindows()

            try:
                sa.delete(self.__share_array_name)
            except:
                self.pym.PY_LOG(False, 'D', self.__log_name, 'share_array:%s has been deleted' % self.__share_array_name)
                

    def display_main_loop(self):
        Tk.mainloop()

    def shut_down_log(self, msg):
        self.pym.PY_LOG(True, 'D', self.__log_name, msg)

    #按鈕單擊事件處理函式
    def _quit(self):
        #結束事件主迴圈，並銷燬應用程式視窗
        self.__root.quit()
        self.__root.destroy()
        self.shut_down_log("quit")

    def show_error_msg_on_toast(self, title, msg):
        messagebox.showerror(title, msg)

    def show_info_msg_on_toast(self, title, msg):
        messagebox.showinfo(title, msg)

    def show_warning_msg_on_toast(self, title, msg):
        messagebox.showwarinig(title, msg)

    def askokcancel_msg_on_toast(self, title, msg):
        return messagebox.askokcancel(title, msg)

    #定義並繫結鍵盤事件處理函式
    def on_key_event(self, event):
        print('you pressed %s'% event.key)
        key_press_handler(event, canvas, toolbar)
        canvas.mpl_connect('key_press_event', on_key_event)

 
