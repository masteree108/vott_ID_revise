import cv2
import os
import sys
import enum
from random import randint
import log as PYM
from _pydecimal import Decimal, Context, ROUND_HALF_UP
import numpy as np

class BBOX_ITEM(enum.Enum):
    py = 0
    px = 1
    ph = 2
    pw = 3

class cv_sift_match():
# private
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


    __video_path = ''
    __video_cap = 0
    __tracker = 0
    __image_debug = [0,0,0]
    __vott_video_fps = 0
    __previous_bbox = []
    __cur_frame = 0
    __debug_img_path = ''
    __debug_img_sw = 0
    __frame_size = []
    __save_crop_img_path = ''
    __cur_crop_objects = []
    __next_crop_objects = []
    __cur_ids = []
    __next_ids = []
    __cur_bboxes = []
    __next_bboxes = []
    __super_resolution_path = "./ESPCN/ESPCN_x4.pb"
    __cur_timestamp = ''
    __next_timestamp = ''

    def __init_super_resolution(self):
        self.sr = cv2.dnn_superres.DnnSuperResImpl_create()
        self.sr.readModel(self.__super_resolution_path)
        self.sr.setModel("espcn",4)

    '''
    def __check_which_frame_number(self, format_value, format_fps):
        for count in range(len(format_fps)):
            if format_value == format_fps[count]:
                return count + 1
    
    def __show_video_with_bounding_box(self, window_name ,frame, wk_value):
        cv2.imshow(window_name, frame)
        cv2.waitKey(wk_value)

    def __check_bbox_shift_over_threshold(self, previous_bbox, current_bbox):
        self.pym.PY_LOG(False, 'E', self.__class__, 'track_failed check, previous_bbox:%s' % previous_bbox)
        self.pym.PY_LOG(False, 'E', self.__class__, 'track_failed check, previous_bbox:%s' % current_bbox)
        X_diff = abs(previous_bbox[0] - current_bbox[0])
        # diff = 0 that equals tracker couldn't trace this bbox
        if X_diff == 0:
            self.pym.PY_LOG(False, 'E', self.__class__, 'track_failed, current_X -previous_X = %.2f' % X_diff)
            self.pym.PY_LOG(False, 'E', self.__class__, 'track_failed, currect_X = bbox[0]: %.2f' % current_bbox[0])
            self.pym.PY_LOG(False, 'E', self.__class__, 'track_failed, previous_X = bbox[0]: %.2f' % previous_bbox[0])
            return True
        Y_diff = abs(previous_bbox[1] - current_bbox[1])
        if Y_diff == 0:
            self.pym.PY_LOG(False, 'W', self.__class__, 'track_failed, current_Y -previous_Y = %.2f'% Y_diff)
            self.pym.PY_LOG(False, 'E', self.__class__, 'track_failed, currect_Y = bbox[1]: %.2f' % current_bbox[1])
            self.pym.PY_LOG(False, 'E', self.__class__, 'track_failed, previous_Y = bbox[1]: %.2f' % previous_bbox[1])
            return True
        return False
    '''

# public
    def __init__(self, video_path, vott_set_fps, frame_size, debug_img_path, debug_img_sw):
        # below(True) = exports log.txt
        self.pym = PYM.LOG(True) 
        self.__video_path = video_path 
        self.__vott_video_fps = vott_set_fps
        self.__frame_size = []
        self.__frame_size = frame_size
        self.__debug_img_path = debug_img_path
        self.__debug_img_sw = debug_img_sw
        self.__init_super_resolution()

    #def __del__(self):
        #deconstructor

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

        return int(index) + 1

    def shut_down_log(self, msg):
        self.pym.PY_LOG(True, 'D', self.__class__, msg)

    def capture_frame_and_save_bboxes(self, label_object_time_in_video, bboxes, ids, next_state):
        # 1. make sure video is existed
        self.__video_cap = cv2.VideoCapture(self.__video_path)
        if not self.__video_cap.isOpened():
            self.pym.PY_LOG(False, 'E', self.__class__, 'open video failed!!.')
            return False

        # 2. reading video strat time at the time that user using VoTT to label trakc object
        # *1000 because CAP_PROP_POS_MESE is millisecond
        self.__video_cap.set(cv2.CAP_PROP_POS_MSEC, label_object_time_in_video*1000)                              
        # ex: start time at 50s
        # self.video_cap.set(cv2.CAP_PROP_POS_MSEC, 50000)
        # self.__video_cap.set(cv2.CAP_PROP_FPS, 15)  #set fps to change video,but not working!!
        
        # 3. save this frame
        frame = self.capture_video_frame(self.__frame_size)
        self.__cur_frame = frame.copy()
        
        if next_state == 0:
            self.__cur_bboxes = bboxes.copy()
            self.__cur_ids = ids.copy()
            self.__cur_timestamp = label_object_time_in_video
        elif next_state == 1:
            self.__next_bboxes = bboxes.copy()
            self.__next_ids = ids.copy()
            self.__next_timestamp = label_object_time_in_video
     
        # for debugging
        if self.__debug_img_sw == 1:
            bbox_colors = []
            for bbox in bboxes:
                bbox_colors.append((randint(64, 255), randint(64, 255), randint(64, 255)))

            for i,bbox in enumerate(bboxes):
                p1 = (int(bbox[BBOX_ITEM.py.value]), int(bbox[BBOX_ITEM.px.value]))
                p2 = (int(bbox[BBOX_ITEM.py.value] + bbox[BBOX_ITEM.ph.value]), \
                    int(bbox[BBOX_ITEM.px.value] + bbox[BBOX_ITEM.pw.value]))
                # below rectangle last parameter = return frame picture
                cv2.rectangle(frame, p1, p2, bbox_colors[i], 4, 0)
                cv2.putText(frame, ids[i], (p1), cv2.FONT_HERSHEY_COMPLEX, 0.8, bbox_colors[i], 1)

            save_debug_img_path = self.__debug_img_path + str(label_object_time_in_video) + '/'
            os.mkdir(save_debug_img_path)
            cv2.imwrite(save_debug_img_path + str(label_object_time_in_video)+'.png', frame)
            self.__save_crop_img_path = save_debug_img_path

    
    def make_ids_img_table(self, next_state):
        ids = []
        crop_objects = []
        size_x = 200
        size_y = 200
        # create black image for fill empty ids_img_table
        img_black = np.zeros([size_x,size_y,3],dtype=np.uint8)
        img_black.fill(0)
        name_for_debug = ''
        
        if next_state == 0:
            ids = self.__cur_ids.copy()
            crop_objects = self.__cur_crop_objects.copy()
            name_for_debug = str(self.__cur_timestamp)
            
        elif next_state == 1:
            ids = self.__next_ids.copy()
            crop_objects = self.__next_crop_objects.copy()
            name_for_debug = str(self.__next_timestamp)


        resize_img = []
        #resize image for combine every images and put on id on the specify image
        for i,img in enumerate(crop_objects):
            img = cv2.resize(img , (size_x, size_y))
            cv2.putText(img, ids[i], (10, 20), cv2.FONT_HERSHEY_COMPLEX, 0.8, (0,0,255), 2)
            resize_img.append(img)

        imgs_table = []
        # below comment out section is decoding binary data to image
        '''
        for i,img in enumerate(crop_objects):
            decode_img = np.asarray(bytearray(img), dtype='uint8')
            decode_img = cv2.imdecode(decode_img, cv2.IMREAD_COLOR)
            imgs_table.append(decode_img)
        '''

        # combine all of images to one image
        amount_of_objs = len(resize_img)
        x_axis = 5
        y_axis = int(amount_of_objs / 5)
        x_left = int(amount_of_objs % 5)
        y_axis_org = y_axis
        if x_left != 0:
            y_axis = y_axis + 1
        
        for y in range(y_axis):
            imgs_table.append([])
            if y == y_axis_org:
                for x in range(x_axis):
                    if x < x_left:
                        imgs_table[y].append(resize_img[x+x_axis*y])
                    else:
                        imgs_table[y].append(img_black)
            else:
                for x in range(x_axis):
                    imgs_table[y].append(resize_img[x+x_axis*y])
       
        cimg = []
        # x axis direction combine
        for i in range(y_axis):
            image = np.concatenate(imgs_table[i], axis=1)
            cimg.append(image)
            #cv2.imshow(str(i), image)

        for i in range(y_axis):
            if i>=1:
                image_all = np.vstack((image_all, cimg[i]))
            else:
                image_all = cimg[i]
        
        if self.__debug_img_sw == 1:
            path = self.__save_crop_img_path + 'image_table_' + name_for_debug + '.png'
            cv2.imwrite(path, image_all)

        if next_state == 0:
            self.__cur_ids_img_table = image_all
        elif next_state == 1:
            self.__next_ids_img_table = image_all

        #cv2.imshow('image table:' + name_for_debug, image_all)
        #cv2.waitKey(0)
        #cv2.destroyAllWindows()

    def crop_people_on_frame(self, next_state):
        bboxes = []
        ids = []
        crop_objects = []
        if next_state == 0:
            bboxes = self.__cur_bboxes.copy()
            ids = self.__cur_ids.copy()
            # below operation(no copy)like c language pointers
            crop_objects = self.__cur_crop_objects
        elif next_state == 1:
            bboxes = self.__next_bboxes.copy()
            ids = self.__next_ids.copy()
            # below operation(no copy)like c language pointers
            crop_objects = self.__next_crop_objects

        for i,bbox in enumerate(bboxes):
            p1 = (int(bbox[BBOX_ITEM.py.value]), int(bbox[BBOX_ITEM.px.value]))
            p2 = (int(bbox[BBOX_ITEM.py.value] + bbox[BBOX_ITEM.ph.value]), \
                int(bbox[BBOX_ITEM.px.value] + bbox[BBOX_ITEM.pw.value]))
            w = int(bbox[BBOX_ITEM.pw.value])
            h = int(bbox[BBOX_ITEM.ph.value])
            x = p1[1]
            y = p1[0]
            crop_img = self.__cur_frame[x:x+w, y:y+h]
            # super resolution 
            crop_img = self.sr.upsample(crop_img)
            crop_img = cv2.pyrUp(crop_img)
            crop_objects.append(crop_img)

            # below comment out section is encoding image to binary date and saving to memory
            '''
            is_success, crop_object = cv2.imencode('.png', crop_img)
            if is_success:
                CB = crop_object.tobytes()
                crop_objects.append(CB)
                self.pym.PY_LOG(False, 'D', self.__class__, 'crop_img(%s) saves to memory successed!!' % ids[i])
            else:
                self.pym.PY_LOG(False, 'E', self.__class__, 'crop_img(%s) saves to memory failed!!' % ids[i])
            '''

            if self.__debug_img_sw == 1:
                path = self.__save_crop_img_path + ids[i] + '.png'
                cv2.imwrite(path, crop_img)

    def get_ids_img_table(self, next_state):
        if next_state == 0:
            return self.__cur_ids_img_table
        elif next_state ==1:
            return self.__next_ids_img_table

    def get_ids_img_table_binary_data(self, next_state):
        name = '_ids_img_table'
        if next_state == 0:
            img = self.__cur_ids_img_table
            name = 'cur' + name
        elif next_state ==1:
            img = self.__next_ids_img_table
            name = 'next' + name

        is_success, bimg = cv2.imencode('.png', img)
        if is_success:
            BI = bimg.tobytes()
            with open(name, 'wb') as f:
                f.write(BI)
                f.flush

            self.pym.PY_LOG(False, 'D', self.__class__, name + ' saves to %s file successed!!' % name)
        else:
            self.pym.PY_LOG(False, 'E', self.__class__, name + ' saves to % file failed!!' % name)

    def check_support_fps(self, vott_video_fps):
        self.__vott_video_fps = vott_video_fps
        if vott_video_fps == 15:
            return True
        # for adding new fps format use, please write it here
        elif vott_video_fps == 6:
            return True
        elif vott_video_fps == 5:
            return True
        else:
            self.pym.PY_LOG(False, 'E', self.__class__, 'This version only could track 5 or 15 fps that user setting on the VoTT')
            return False


    def capture_video_frame(self, frame_size):
        ok, frame = self.__video_cap.read()
        if not ok:
            self.pym.PY_LOG(False, 'E', self.__class__, 'open video failed!!')
            sys.exit()
        try:                           
            frame = cv2.resize(frame, (frame_size[0], frame_size[1]))                                                                         
        except:      
            self.pym.PY_LOG(False, 'E', "frame resize failed!!")
        return frame





    ''' 
    def get_label_frame_number(self, format_value):
        # check which frame that user use VoTT tool to label
        fps = self.__vott_video_fps
        if fps == 15:
            return self.__check_which_frame_number(format_value, self.__format_15fps)
        # for adding new fps format use, please write it here
        elif fps == 6:
            return self.__check_which_frame_number(format_value, self.__format_6fps)
        elif fps == 5:
            return self.__check_which_frame_number(format_value, self.__format_5fps)
    
    def get_now_format_value(self, frame_count):
        # check which frame that user use VoTT tool to label
        fps = self.__vott_video_fps
        fc = frame_count -1
        if fps == 15:
            return self.__format_15fps[fc]
        elif fps == 6:
            return self.__format_6fps[fc]
        elif fps == 5:
            return self.__format_5fps[fc]
   
    def use_ROI_select(self, ROI_window_name, frame):
        cv2.namedWindow(ROI_window_name, cv2.WINDOW_NORMAL)                                                   
        cv2.resizeWindow(ROI_window_name, 1280, 720)
        bbox = cv2.selectROI(ROI_window_name, frame, False)
        cv2.destroyWindow(ROI_window_name)
        return bbox

    def draw_boundbing_box_and_get(self, frame, ids):
        ok, bboxes = self.__tracker.update(frame)
        track_state = {'no_error': True, 'failed_id': 'no_id'}
        if ok:
            for i, newbox in enumerate(bboxes):
                p1 = (int(newbox[0]), int(newbox[1]))
                p2 = (int(newbox[0] + newbox[2]), int(newbox[1] + newbox[3]))
                # below rectangle last parameter = return frame picture
                cv2.rectangle(frame, p1, p2, self.__bbox_colors[i], 4, 0)
                # add ID onto video
                cv2.putText(frame, ids[i], (p1), cv2.FONT_HERSHEY_COMPLEX, 2, self.__bbox_colors[i], 3)

        else:
            track_state.update({'no_error': False, 'failed_id':"no_id"})
            for i, newbox in enumerate(bboxes):
                self.pym.PY_LOG(False, 'W', self.__class__, 'track_failed_check id: %s' % ids[i])
                if self.__check_bbox_shift_over_threshold(self.__previous_bbox[i], newbox):
                    track_state.update({'no_error': False, 'failed_id':ids[i]})
                    break
            bboxes = [0,0,0,0]
            if self.__image_debug[IMAGE_DEBUG.SW_VWB.value] == 1 or \
               self.__image_debug[IMAGE_DEBUG.SE_IWB.value] == 1 or \
               self.__image_debug[IMAGE_DEBUG.SE_VWB.value] == 1 :
                cv2.putText(frame, "Tracking failure detected", (100, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 3, 255), 2)
                self.pym.PY_LOG(False, 'E', self.__class__, 'Tarcking failre detected')
            else:
                self.pym.PY_LOG(False, 'E', self.__class__, 'Tarcking failre detected')
                

        if self.__image_debug[IMAGE_DEBUG.SW_VWB.value] == 1:
            # showing video with bounding box
            self.__show_video_with_bounding_box(self.window_name ,frame, 1)
         
        self.__previous_bbox = []
        for i, bbox in enumerate(bboxes):
            self.__previous_bbox.append(bbox)
        #self.__previous_bbox.append(bboxes)
        return bboxes, track_state
    
    def use_waitKey(self, value):
        cv2.waitKey(value)

    def show_video_format_info(self):
        self.pym.PY_LOG(False, 'D', self.__class__, '===== source video format start =====')
        wid = int(self.__video_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        hei = int(self.__video_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        frame_rate = int(self.__video_cap.get(cv2.CAP_PROP_FPS))
        frame_num = int(self.__video_cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.pym.PY_LOG(False, 'D', self.__class__, 'video width: %d' % wid)
        self.pym.PY_LOG(False, 'D', self.__class__, 'height: %d' % hei)
        
        # below framenum / framerate = video length
        self.pym.PY_LOG(False, 'D', self.__class__, 'framerate: %.5f' % frame_rate)
        self.pym.PY_LOG(False, 'D', self.__class__, 'framenum: %d' % frame_num)
        video_length = float(frame_num / frame_rate)
        self.pym.PY_LOG(False, 'D', self.__class__, 'video length: %.5f secs' % video_length)
        self.pym.PY_LOG(False, 'D', self.__class__, '===== source video format over =====')
    
    def get_now_frame_timestamp_DP(self, frame_count):
        fc = frame_count -1
        fps = self.__vott_video_fps
        if fps == 15:
            return self.__frame_timestamp_DP_15fps[fc]
        elif fps == 6: 
            return self.__frame_timestamp_DP_6fps[fc]
        elif fps == 5: 
            return self.__frame_timestamp_DP_5fps[fc]
    
    
    def set_video_strat_frame(self, time):
        self.__video_cap.set(cv2.CAP_PROP_POS_MSEC, time*1000)                              

    def destroy_debug_window(self):
        cv2.destroyWindow(self.window_name)

    def get_source_video_fps(self):
        return int(self.__video_cap.get(cv2.CAP_PROP_FPS))

    def get_every_second_last_frame_timestamp(self):
        fps = self.__vott_video_fps
        if fps == 15:
            return self.__frame_timestamp_DP_15fps[fps - 1]
        elif fps == 6:
            return self.__frame_timestamp_DP_6fps[fps - 1]   
        elif fps == 5:
            return self.__frame_timestamp_DP_5fps[fps - 1]   

    def get_pick_up_frame_interval(self, vott_video_fps):
        source_video_fps = self.get_source_video_fps()
        self.pym.PY_LOG(False, 'D', self.__class__, 'source_video_fps: %d' % source_video_fps)
                                
        interval = float(source_video_fps / vott_video_fps)
        
        # round 
        interval = Context(prec=1, rounding=ROUND_HALF_UP).create_decimal(interval)
        self.pym.PY_LOG(False, 'D', self.__class__, 'pick up frame interval : %.2f' % interval)                                                                  
        return interval

    def get_update_frame_interval(self, tracking_fps):
        source_video_fps = self.get_source_video_fps()
                                
        interval = float(source_video_fps / tracking_fps)
        
        # round 
        interval = Context(prec=1, rounding=ROUND_HALF_UP).create_decimal(interval)
        self.pym.PY_LOG(False, 'D', self.__class__, 'update frame interval : %.2f' % interval)                                                                  
        return interval
    '''
