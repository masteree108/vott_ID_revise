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
    __cur_crop_objects_15_unit = []
    __next_crop_objects = []
    __next_crop_objects_15_unit = []
    __cur_ids = []
    __cur_ids_15_unit = []
    __next_ids = []
    __next_ids_15_unit = []
    __cur_bboxes = []
    __next_bboxes = []
    __super_resolution_path = "./ESPCN/ESPCN_x4.pb"
    __cur_timestamp = ''
    __next_timestamp = ''
    __cur_destors = []
    __next_destors = []
    __match_threshold = 3
    __cur_ids_img_table = []
    __cur_no_ids_img_table = []
    __next_ids_img_table = []
    __next_no_ids_img_table = []


    def __init_super_resolution(self):
        self.sr = cv2.dnn_superres.DnnSuperResImpl_create()
        self.sr.readModel(self.__super_resolution_path)
        self.sr.setModel("espcn",4)

    def __find_descriptors(self, imgs):
        des_list = []
        for img in imgs:
            kp, des = self.sift.detectAndCompute(img, None)
            des_list.append(des)
        return des_list.copy()

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
        self.sift = cv2.xfeatures2d.SIFT_create(1000)

    def __del__(self):
        #deconstructor
        self.shut_down_log("over")

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
            self.__cur_ids_15_unit.append([])
            ct = 0
            for i,id_val in enumerate(ids):
                if i % 15 == 0 and i != 0:
                    self.__cur_ids_15_unit.append([])
                    ct = ct + 1
                self.__cur_ids_15_unit[ct].append(id_val)

        elif next_state == 1:
            self.__next_bboxes = bboxes.copy()
            self.__next_ids = ids.copy()
            self.__next_timestamp = label_object_time_in_video
            self.__next_ids_15_unit.append([])
            ct = 0
            for i,id_val in enumerate(ids):
                if i % 15 == 0 and i != 0:
                    self.__next_ids_15_unit.append([])
                    ct = ct + 1 
                self.__next_ids_15_unit[ct].append(id_val)

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

    def get_crop_objects_15_unit_size(self, next_state):
        if next_state == 0:
            return len(self.__cur_crop_objects_15_unit)
        elif next_state == 1:
            return len(self.__next_crop_objects_15_unit)

    def make_ids_img_table(self, next_state, index):
        ids = []
        crop_objects = []
        size_x = 200
        size_y = 200
        # create black image for fill empty ids_img_table
        img_black = np.zeros([size_x,size_y,3],dtype=np.uint8)
        img_black.fill(0)
        name_for_debug = ''
        
        if next_state == 0:
            ids = self.__cur_ids_15_unit[index].copy()
            crop_objects = self.__cur_crop_objects_15_unit[index].copy()
            name_for_debug = str(self.__cur_timestamp)
            
        elif next_state == 1:
            ids = self.__next_ids_15_unit[index].copy()
            crop_objects = self.__next_crop_objects_15_unit[index].copy()
            name_for_debug = str(self.__next_timestamp)

        resize_img = []
        resize_img_no_id = []

        #resize image for combine every images and put on id on the specify image
        for i,img in enumerate(crop_objects):
            img = cv2.copyMakeBorder(img, 100, 0, 10, 10, cv2.BORDER_CONSTANT, value=(0,0,0))
            img_no_id = img.copy()
            img = cv2.resize(img , (size_x, size_y))
            cv2.putText(img, ids[i], (10, 20), cv2.FONT_HERSHEY_COMPLEX, 0.8, (0,0,255), 2)
            img_no_id = cv2.resize(img_no_id , (size_x, size_y))
            resize_img.append(img)
            resize_img_no_id.append(img_no_id)

        imgs_table = []
        imgs_table_no_id = []
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
            imgs_table_no_id.append([])
            if y == y_axis_org:
                for x in range(x_axis):
                    if x < x_left:
                        imgs_table[y].append(resize_img[x+x_axis*y])
                        imgs_table_no_id[y].append(resize_img_no_id[x+x_axis*y])
                    else:
                        imgs_table[y].append(img_black)
                        imgs_table_no_id[y].append(img_black)
            else:
                for x in range(x_axis):
                    imgs_table[y].append(resize_img[x+x_axis*y])
                    imgs_table_no_id[y].append(resize_img_no_id[x+x_axis*y])

        # if y_axis < 3 row, we add it with block image to 3 row
        if y_axis != 3:
            for y in range(y_axis, 3):
                imgs_table.append([])
                imgs_table_no_id.append([])
                for x in range(5):
                    imgs_table[y].append(img_black)
                    imgs_table_no_id[y].append(img_black)

        cimg = []
        cimg_no_id = []
        # x axis direction combine
        #for i in range(y_axis):
        for i in range(3):
            image = np.concatenate(imgs_table[i], axis=1)
            image_no_id = np.concatenate(imgs_table_no_id[i], axis=1)
            cimg.append(image)
            cimg_no_id.append(image_no_id)
            #cv2.imshow(str(i), image)

        #for i in range(y_axis):
        for i in range(3):
            if i>=1:
                image_all = np.vstack((image_all, cimg[i]))
                image_all_no_id = np.vstack((image_all_no_id, cimg_no_id[i]))
            else:
                image_all = cimg[i]
                image_all_no_id = cimg_no_id[i]
        
        if self.__debug_img_sw == 1:
            path = self.__save_crop_img_path + 'image_table_' + name_for_debug + '_' + str(index) + '.png'
            path_no_id = self.__save_crop_img_path + 'no_id_image_table_' + name_for_debug + '_' + str(index) + '.png'
            cv2.imwrite(path, image_all)
            cv2.imwrite(path_no_id, image_all_no_id)

        if next_state == 0:
            self.__cur_ids_img_table.append(image_all)
            self.__cur_no_ids_img_table.append(image_all_no_id)
        elif next_state == 1:
            self.__next_ids_img_table.append(image_all)
            self.__next_no_ids_img_table.append(image_all_no_id)

        #cv2.imshow('image table:' + name_for_debug, image_all)
        #cv2.waitKey(0)
        #cv2.destroyAllWindows()

    def crop_people_on_frame(self, next_state):
        bboxes = []
        ids = []
        crop_objects = []
        crop_objects_15_unit = []
        if next_state == 0:
            bboxes = self.__cur_bboxes.copy()
            ids = self.__cur_ids.copy()
            # below operation(no copy)like c language pointers
            crop_objects = self.__cur_crop_objects
            crop_objects_15_unit = self.__cur_crop_objects_15_unit
        elif next_state == 1:
            bboxes = self.__next_bboxes.copy()
            ids = self.__next_ids.copy()
            # below operation(no copy)like c language pointers
            crop_objects = self.__next_crop_objects
            crop_objects_15_unit = self.__next_crop_objects_15_unit
        
        # 15 people be an 1 unit
        ct = 0
        crop_objects_15_unit.append([])
        for i,bbox in enumerate(bboxes):
            if i % 15 == 0 and i != 0:
              ct = ct + 1
              crop_objects_15_unit.append([])
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
            #crop_img = cv2.pyrUp(crop_img)
            crop_objects.append(crop_img)
            crop_objects_15_unit[ct].append(crop_img)
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

    def save_ids_img_table(self, next_state, index):
        name = '_ids_img_table'
        if next_state == 0:
            img = self.__cur_ids_img_table[index]
            name = 'cur' + name
        elif next_state ==1:
            img = self.__next_ids_img_table[index]
            name = 'next' + name
        
        cv2.imwrite(name +'_'+ str(index)+'.png', img)
        '''
        is_success, bimg = cv2.imencode('.png', img)
        if is_success:
            BI = bimg.tobytes()
            with open(name, 'wb') as f:
                f.write(BI)
                f.flush

            self.pym.PY_LOG(False, 'D', self.__class__, name + ' saves to %s file successed!!' % name)
        else:
            self.pym.PY_LOG(False, 'E', self.__class__, name + ' saves to % file failed!!' % name)
        '''
    def save_no_ids_img_table(self, next_state, index):
        name = '_no_ids_img_table'
        if next_state == 0:
            img = self.__cur_no_ids_img_table[index]
            name = 'cur' + name
        elif next_state ==1:
            img = self.__next_no_ids_img_table[index]
            name = 'next' + name
        
        cv2.imwrite(name +'_'+ str(index)+'.png', img)

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
            self.pym.PY_LOG(False, 'E', self.__class__, "frame resize failed!!")
        return frame

    def feature_extraction(self, next_state):
        crop_objects = []
        if next_state == 0:
            crop_objects = self.__cur_crop_objects.copy()
            self.__cur_destors = self.__find_descriptors(crop_objects)
        elif next_state == 1:
            crop_objects = self.__next_crop_objects.copy()
            self.__next_destors = self.__find_descriptors(crop_objects)

    def feature_matching_get_new_id(self, id_val):
        bf = cv2.BFMatcher()
        match_list = []
        find_id = 'no_id'
        index = 0

        try:
            id_array = np.array(self.__next_ids)
            index = np.argwhere(id_array == id_val)
            index = int(index)
            self.pym.PY_LOG(False, 'D', self.__class__, "find id:%s descriptor index!!" % str(index))
        except:
            self.pym.PY_LOG(False, 'E', self.__class__, "find id:%s descriptor index error!!" % id_val)
            pass

        # read this id's descriptor
        next_id_des = self.__next_destors[index]
        try:
            for cur_des in self.__cur_destors:
                matches = bf.knnMatch(next_id_des, cur_des, k=2)
                good = []
                for m, n in matches:
                    if m.distance < 0.75 *n.distance:
                        good.append([m])
                match_list.append(len(good))
        except:
            self.pym.PY_LOG(False, 'E', self.__class__, "find id:%s error!!" % id_val)
            pass

        if len(match_list) != 0:
            if max(match_list) > self.__match_threshold:
                find_id_index = match_list.index(max(match_list))
                find_id = self.__cur_ids[find_id_index]
                                
        return find_id,index
    
    def show_id_img(self, index):
        cv2.namedWindow('id', cv2.WINDOW_NORMAL)
        img = self.__next_crop_objects[index]
        img = cv2.resize(img , (300, 300))
        cv2.imshow('id', img)

    def close_window(self):
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    def wait_key(self, val):
        cv2.waitKey(val)

    def destroy_window(self):
        cv2.destroyAllWindows()

    def show_ids_img_table(self, next_state):
        size = self.get_crop_objects_15_unit_size(next_state)
        for i in range(size):
            if next_state == 0:
                img = self.__cur_ids_img_table[i]
            else:
                img = self.__next_ids_img_table[i]
            
            #img = cv2.resize(img , (1280, 720))
            cv2.imshow('ids_image_table_'+str(i), img)

