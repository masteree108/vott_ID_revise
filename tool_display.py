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

#public
    def __init__(self):
        self.pym = PYM.LOG(True)
        matplotlib.use('TkAgg')

        #規定窗口大小
        self.__root.geometry('2000x2000')
        self.__root.title("統一VoTT json 檔案內的人物ID")
        figure, self.ax = plt.subplots(1, 1, figsize=(16, 8))
        image = cv2.imread("default_img/logo_combine.jpg")
        self.ax.imshow(image)

        #放置標籤
        #self.label = Tk.Label(self.__root,text = 'pictures will show in this place', image = None)   #創建一個標籤
        #self.label.pack()

        #把繪製的圖形顯示到tkinter視窗上
        #self.__canvas = self.update_image(figure)
        self.update_image(figure)

        #把matplotlib繪製圖形的導航工具欄顯示到tkinter視窗上
        toolbar = NavigationToolbar2TkAgg(self.__canvas, self.__root)
        toolbar.update()
        self.__canvas._tkcanvas.pack(side = Tk.TOP, fill = Tk.BOTH, expand = 1)

        # quit button
        quit_btn = Tk.Button(master = self.__root, text = 'Quit', command = self._quit)
        #quit_btn.pack(side = Tk.BOTTOM)
        quit_btn.pack(side = Tk.RIGHT)
        
        # open image button
        open_img_btn = Tk.Button(master = self.__root, text='選擇1張圖片', command = self.open_image)  #設置按鈕，並給它openpicture命令
        open_img_btn.pack(side = Tk.RIGHT)

    def update_image(self, figure):
        self.__canvas = FigureCanvasTkAgg(figure, master = self.__root)
        self.__canvas.draw()
        self.__canvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand = 1)
        #return canvas

    def open_image(self):
        filename = filedialog.askopenfilename()     #獲取文件全路徑
        self.__open_image_path = filename
        #img = ImageTk.PhotoImage(Image.open(filename))   #tkinter只能打開gif文件，這裏用PIL庫
        # 打開jpg格式的文件
        #self.label.config(image = img)    #用config方法將圖片放置在標籤中       
        if os.path.isfile(filename):
            self.pym.PY_LOG(False, 'D', self.__log_name, 'open image path:' + '%s' % filename)
            image = cv2.imread(filename)
            self.ax.imshow(image)
            #self.update_image(figure)

    def display_main_loop(self):
        Tk.mainloop()
        #if os.path.isfile(self.__open_img_path):
            #self.pym.PY_LOG(False, 'D', self.__log_name, 'open image path:' + '%s' % self.__open_img_path)
            #image = cv2.imread(self.__open_img_path)
            #self.ax.imshow(image)

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

