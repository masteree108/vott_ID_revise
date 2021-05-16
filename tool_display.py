import cv2
import sys
import os
import tkinter as Tk
import matplotlib
import matplotlib.pyplot as plt
from PIL import Image, ImageTk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk as NavigationToolbar2TkAgg
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure
from tkinter import filedialog       #獲取文件全路徑
import log as PYM

class tool_display():

#private
    __log_name = '< class tool display>'
    __root = Tk.Tk()
    __open_img_path = ''
    __canvas = 0
    __json_data_path = ''

#public
    def __init__(self, td_que, fm_process_que):

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

        # quit button
        quit_btn = Tk.Button(master = self.__root, text = 'Quit', command = self._quit)
        #quit_btn.pack(side = Tk.BOTTOM)
        quit_btn.pack(side = Tk.RIGHT)
        
        # open image button, this is for testing function
        open_img_btn = Tk.Button(master = self.__root, text='選擇1張圖片', command = self.open_image)  #設置按鈕，並給它openpicture命令
        open_img_btn.pack(side = Tk.RIGHT)
        
        # get *.json data path button
        get_json_data_path_btn = Tk.Button(master = self.__root, text='json data path', command = self.find_json_file_path)  #設置按鈕，並給它openpicture命令
        get_json_data_path_btn.pack(side = Tk.RIGHT)

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
        file_path = filedialog.askdirectory()     #獲取文件全路徑
        if os.path.isdir(file_path):
            self.pym.PY_LOG(False, 'D', self.__log_name, 'json file path:' + '%s' % file_path)
            self.fm_process_queue.put("json_file_path:" + str(file_path)); 
            self.label.config(text = 'json file path:' + file_path )  
        else:
            self.pym.PY_LOG(False, 'D', self.__log_name, 'json file path:' + '%s' % file_path + 'is not existed!!')
            self.label.config(text = 'json file path is not existed!!' )  


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

    #定義並繫結鍵盤事件處理函式
    def on_key_event(self, event):
        print('you pressed %s'% event.key)
        key_press_handler(event, canvas, toolbar)
        canvas.mpl_connect('key_press_event', on_key_event)

