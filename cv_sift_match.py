import cv2
import os
import sys
import enum
from random import randint
import log as PYM
from _pydecimal import Decimal, Context, ROUND_HALF_UP
import numpy as np

class cv_sift_match():
# private
    __video_path = ''
    __video_cap = 0
    __image_debug = [0,0,0]
    __vott_video_fps = 0
    __debug_img_path = ''
    __debug_img_sw = 0
    __frame_size = []
    __save_crop_img_path = ''
    __cur_crop_objects = []
    __cur_crop_objects_12_unit = []
    #wb = with bbox
    __cur_crop_objects_12_unit_wb = []
    __next_crop_objects = []
    __next_crop_objects_12_unit = []
    __next_crop_objects_12_unit_wb = []
    __cur_ids = []
    __cur_ids_12_unit = []
    __next_ids = []
    __next_ids_12_unit = []
    __cur_bboxes = []
    __next_bboxes = []
    __super_resolution_path = "./ESPCN/ESPCN_x4.pb"
    __cur_timestamp = ''
    __next_timestamp = ''
    __cur_destors = []
    __next_destors = []
    __SIFT_match_point_min = 3
    __cur_ids_img_table = []
    __cur_no_ids_img_table = []
    __next_ids_img_table = []
    __next_no_ids_img_table = []
    __bbox_colors = []
    __combine_table = []
    __combine_table_path = "./.system/combine"
    __frame_img_path = "./result/frame_image/"
    __SIFT_feature_match_point = []
    __SIFT_feature_match_ids = []
    __IoU_predict_percentage = []
    __IoU_predict_ids = []
    __SIFT_match_point_threshold = 10
    __IoU_match_threshold = 30.00
    __final_predict_ids = []

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
        self.init_for_next_round()
        self.__SIFT_feature_match_point = []
        self.__SIFT_feature_match_ids = []
        self.__final_predict_ids = []

    def __del__(self):
        #deconstructor
        self.shut_down_log("over")

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
        self.__bbox_colors = []
        for bbox in bboxes:
            self.__bbox_colors.append((randint(64, 255), randint(64, 255), randint(64, 255)))

        frame = self.capture_video_frame(self.__frame_size)
        self.__cur_frame = frame.copy()
        self.__cur_frame_with_bbox = frame.copy()
        for i,bbox in enumerate(bboxes):
            p1 = (int(bbox[0]), int(bbox[1]))
            p2 = (int(bbox[0] + bbox[2]), \
                int(bbox[1] + bbox[3]))
            # below rectangle last parameter = return frame picture
            cv2.rectangle(self.__cur_frame_with_bbox, p1, p2, self.__bbox_colors[i], 2, 0)

        if next_state == 0:
            self.__cur_bboxes = bboxes.copy()
            self.__cur_ids = ids.copy()
            self.__cur_timestamp = label_object_time_in_video
            self.__cur_ids_12_unit.append([])

            if self.__debug_img_sw == 1:
                self.__IoU_frame_with_cur_bbox = self.__cur_frame_with_bbox.copy()
            ct = 0
            for i,id_val in enumerate(ids):
                if i % 12 == 0 and i != 0:
                    self.__cur_ids_12_unit.append([])
                    ct = ct + 1
                self.__cur_ids_12_unit[ct].append(id_val)

        elif next_state == 1:
            self.__next_bboxes = bboxes.copy()
            self.__next_ids = ids.copy()
            self.__next_timestamp = label_object_time_in_video
            self.__next_ids_12_unit.append([])
            ct = 0
            for i,id_val in enumerate(ids):
                if i % 12 == 0 and i != 0:
                    self.__next_ids_12_unit.append([])
                    ct = ct + 1 
                self.__next_ids_12_unit[ct].append(id_val)

        # save full frame image for user finding id position
        for i,bbox in enumerate(bboxes):
            p1 = (int(bbox[0]), int(bbox[1]))
            p2 = (int(bbox[0] + bbox[2]), \
                int(bbox[1] + bbox[3]))
            # below rectangle last parameter = return frame picture
            cv2.rectangle(frame, p1, p2, self.__bbox_colors[i], 2, 0)
            cv2.putText(frame, ids[i], (p1), cv2.FONT_HERSHEY_COMPLEX, 0.8, self.__bbox_colors[i], 1)

            if os.path.isdir(self.__frame_img_path) == 0:
                os.mkdir(self.__frame_img_path)
            cv2.imwrite(self.__frame_img_path + str(label_object_time_in_video)+'.png', frame)

        # for debugging
        if self.__debug_img_sw == 1:
            save_debug_img_path = self.__debug_img_path + str(label_object_time_in_video) + '/'
            os.mkdir(save_debug_img_path)
            cv2.imwrite(save_debug_img_path + str(label_object_time_in_video)+'.png', frame)
            self.__save_crop_img_path = save_debug_img_path

    def get_crop_objects_12_unit_size(self, next_state):
        if next_state == 0:
            return len(self.__cur_crop_objects_12_unit)
        elif next_state == 1:
            return len(self.__next_crop_objects_12_unit)

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
            ids = self.__cur_ids_12_unit[index].copy()
            crop_objects = self.__cur_crop_objects_12_unit_wb[index].copy()
            name_for_debug = str(self.__cur_timestamp)
            
        elif next_state == 1:
            ids = self.__next_ids_12_unit[index].copy()
            crop_objects = self.__next_crop_objects_12_unit_wb[index].copy()
            name_for_debug = str(self.__next_timestamp)

        resize_img = []
        resize_img_no_id = []

        #resize image for combine every images and put on id on the specify image
        for i,img in enumerate(crop_objects):
            img = cv2.copyMakeBorder(img, 100, 0, 10, 10, cv2.BORDER_CONSTANT, value=(0,0,0))
            img_no_id = img.copy()
            img = cv2.resize(img , (size_x, size_y))
            if ids[i] != 'id_nnn':
                cv2.putText(img, ids[i], (10, 20), cv2.FONT_HERSHEY_COMPLEX, 0.8, (0,0,255), 2)
            else:
                cv2.putText(img, ids[i], (10, 20), cv2.FONT_HERSHEY_COMPLEX, 0.8, (0,255,0), 2)
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
            
        x_axis = 4
        y_axis = int(amount_of_objs / x_axis)
        x_left = int(amount_of_objs % x_axis)
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

        # if y_axis < 3 row, we add it with black image to 3 row
        fix_row = 3
        if y_axis != fix_row:
            for y in range(y_axis, fix_row):
                imgs_table.append([])
                imgs_table_no_id.append([])
                for x in range(x_axis):
                    imgs_table[y].append(img_black)
                    imgs_table_no_id[y].append(img_black)

        cimg = []
        cimg_no_id = []
        # x axis direction combine
        #for i in range(y_axis):
        for i in range(fix_row):
            image = np.concatenate(imgs_table[i], axis=1)
            image_no_id = np.concatenate(imgs_table_no_id[i], axis=1)
            cimg.append(image)
            cimg_no_id.append(image_no_id)
            #cv2.imshow(str(i), image)

        #for i in range(y_axis):
        for i in range(fix_row):
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

    def deal_with_one_frame_equal_12_but_another_more_than_12(self):
        # create black image for fill empty ids_img_table
        img_black_full = np.zeros([600,800,3],dtype=np.uint8)
        img_black_full.fill(0)
        index = abs(len(self.__cur_ids_img_table) - len(self.__next_ids_img_table))
        for_debug_save_image = 0
        
        if len(self.__cur_ids_img_table) > len(self.__next_ids_img_table):
            for_debug_save_image = 1
            name_for_debug = str(self.__next_timestamp)
            diff = abs(len(self.__cur_ids_img_table)-len(self.__next_ids_img_table))
            for i in range(diff):
                self.__next_ids_img_table.append(img_black_full)
                self.__next_no_ids_img_table.append( img_black_full)

        elif len(self.__cur_ids_img_table) < len(self.__next_ids_img_table):
            for_debug_save_image = 1
            name_for_debug = str(self.__cur_timestamp)
            diff = abs(len(self.__cur_ids_img_table)-len(self.__next_ids_img_table))
            for i in range(diff):
                self.__cur_no_ids_img_table.append(img_black_full)
                self.__cur_ids_img_table.append(img_black_full)

        if self.__debug_img_sw == 1 and for_debug_save_image == 1:
            path = self.__save_crop_img_path + 'image_table_' + name_for_debug + '_' + str(index) + '.png'
            path_no_id = self.__save_crop_img_path + 'no_id_image_table_' + name_for_debug + '_' + str(index) + '.png'
            cv2.imwrite(path, img_black_full)
            cv2.imwrite(path_no_id, img_black_full)

    def crop_people_on_frame(self, next_state):
        bboxes = []
        ids = []
        crop_objects = []
        crop_objects_12_unit = []
        crop_objects_12_unit_wb = []
        if next_state == 0:
            bboxes = self.__cur_bboxes.copy()
            ids = self.__cur_ids.copy()
            # below operation(no copy)like c language pointers
            crop_objects = self.__cur_crop_objects
            crop_objects_12_unit = self.__cur_crop_objects_12_unit
            crop_objects_12_unit_wb = self.__cur_crop_objects_12_unit_wb
        elif next_state == 1:
            bboxes = self.__next_bboxes.copy()
            ids = self.__next_ids.copy()
            # below operation(no copy)like c language pointers
            crop_objects = self.__next_crop_objects
            crop_objects_12_unit = self.__next_crop_objects_12_unit
            crop_objects_12_unit_wb = self.__next_crop_objects_12_unit_wb
        
        # 12 people be an 1 unit
        ct = 0
        offset = 15
        crop_objects_12_unit.append([])
        crop_objects_12_unit_wb.append([])
        # bbox = (left, top, width, height)
        for i,bbox in enumerate(bboxes):
            if i % 12 == 0 and i != 0:
              ct = ct + 1
              crop_objects_12_unit.append([])
              crop_objects_12_unit_wb.append([])
            p1 = (int(bbox[0]), int(bbox[1]))
            p2 = (int(bbox[0] + bbox[2]), \
                int(bbox[1] + bbox[3]))
            w = int(bbox[2])
            h = int(bbox[3])
            x = p1[0]
            y = p1[1]
            crop_img = self.__cur_frame[y:y+h, x:x+w]

            # if the bbox+-offset is exceeds the range of frame, just do below things
            xl = x - offset
            if xl < 0:
                xl = 0

            xr = x + w + offset
            if xr > self.__frame_size[0]:
                xr = self.__frame_size[0] -5

            yt = y - offset
            if yt < 0:
                yt = 0

            yd = y + h + offset
            if yd > self.__frame_size[1]:
                yd = self.__frame_size[1] - 5
            crop_img_wb = self.__cur_frame_with_bbox[yt:yd, xl:xr]
            # super resolution 
            crop_img = self.sr.upsample(crop_img)
            crop_img = cv2.detailEnhance(crop_img, sigma_s=15, sigma_r=0.2)
            crop_img_wb = self.sr.upsample(crop_img_wb)
            crop_objects.append(crop_img)
            crop_objects_12_unit[ct].append(crop_img)
            crop_objects_12_unit_wb[ct].append(crop_img_wb)

            '''
            self.pym.PY_LOG(False, 'D', self.__class__, 'crop_img(%s) saves to memory failed!!' % ids[i])
            self.pym.PY_LOG(False, 'D', self.__class__, 'frame_size[0]:%d' % self.__frame_size[0])
            self.pym.PY_LOG(False, 'D', self.__class__, 'frame_size[1]:%d' % self.__frame_size[1])
            self.pym.PY_LOG(False, 'D', self.__class__, 'w:%d' % w)
            self.pym.PY_LOG(False, 'D', self.__class__, 'h:%d' % h)
            self.pym.PY_LOG(False, 'D', self.__class__, 'x:%d' % x)
            self.pym.PY_LOG(False, 'D', self.__class__, 'y:%d' % y)
            self.pym.PY_LOG(False, 'D', self.__class__, 'xl:%d' % xl)
            self.pym.PY_LOG(False, 'D', self.__class__, 'xr:%d' % xr)
            self.pym.PY_LOG(False, 'D', self.__class__, 'yt:%d' % yt)
            self.pym.PY_LOG(False, 'D', self.__class__, 'yd:%d' % yd)
            '''
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

    def combine_cur_next_img(self):
        #__cur_no_ids_img_table = []
        #__next_ids_img_table = []
        #__next_no_ids_img_table = []
        self.__combine_table = []
        for i in range(len(self.__cur_ids_img_table)):
            img1 = cv2.copyMakeBorder(self.__cur_ids_img_table[i], 0, 0, 10, 50,cv2.BORDER_CONSTANT)
            img2 = cv2.copyMakeBorder(self.__next_no_ids_img_table[i], 0, 0, 10, 50,cv2.BORDER_CONSTANT)
            vis = np.concatenate((img1, img2), axis=1)
            cv2.imwrite(self.__combine_table_path + str(i) + ".png", vis)

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
        des_error = 0

        try:
            id_array = np.array(self.__next_ids)
            index = np.argwhere(id_array == id_val)
            if len(index) == 1:
                index = int(index)
                self.pym.PY_LOG(False, 'D', self.__class__, "find id:%s descriptor index!!" % str(index))
            else:
                index = int(index[0])
                self.pym.PY_LOG(False, 'D', self.__class__, "find id:%s descriptor index!!" % str(index))
        except:
            self.pym.PY_LOG(False, 'E', self.__class__, "find id:%s descriptor index error!!" % id_val)
            des_error = 1
            pass
        
        if des_error == 1:
            self.pym.PY_LOG(False, 'E', self.__class__, "index:%s" % str(index))

        try:
            # read this id's descriptor
            next_id_des = self.__next_destors[index]
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

        feature_match_point = 0
        if len(match_list) != 0:
            max_val = max(match_list)
            feature_match_point = max_val
            self.pym.PY_LOG(False, 'E', self.__class__, "max_val:%d" % max_val)
            
            if max_val > self.__SIFT_match_point_min:
                self.__SIFT_feature_match_point.append(int(max_val))
                find_id_index = match_list.index(max_val)
                find_id = self.__cur_ids[find_id_index]
                self.__SIFT_feature_match_ids.append(find_id)
            else:
                self.__SIFT_feature_match_point.append(0)
                self.__SIFT_feature_match_ids.append('id_???')
                
        return find_id, index, feature_match_point
    
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
        size = self.get_crop_objects_12_unit_size(next_state)
        for i in range(size):
            if next_state == 0:
                img = self.__cur_ids_img_table[i]
            else:
                img = self.__next_ids_img_table[i]
            
            #img = cv2.resize(img , (1280, 720))
            cv2.imshow('ids_image_table_'+str(i), img)


    def IOU_check(self):
        self.pym.PY_LOG(False, 'D', self.__class__, "IoU method")
        save_debug_img_path = self.__debug_img_path
        self.pym.PY_LOG(False, 'D', self.__class__, "--------------------IoU match------------------")
        # for debugging
        if self.__debug_img_sw == 1:
            for i,bbox in enumerate(self.__next_bboxes):
                p1 = (int(bbox[0]), int(bbox[1]))
                p2 = (int(bbox[0] + bbox[2]), \
                    int(bbox[1] + bbox[3]))
                # below rectangle last parameter = return frame picture
                cv2.rectangle(self.__IoU_frame_with_cur_bbox, p1, p2, self.__bbox_colors[i], 2, 0)

            cv2.imwrite(save_debug_img_path + 'IoU'+'.png', self.__IoU_frame_with_cur_bbox)

        self.__IoU_predict_percentage = []
        self.__IoU_predict_ids = []
        iou_temp = []
        for i,nbbox in enumerate(self.__next_bboxes):
            iou_temp = []
            for j,cbbox in enumerate(self.__cur_bboxes):
                xA = max(nbbox[0], cbbox[0])
                #print("xA:%.2f" % xA)
                yA = max(nbbox[1], cbbox[1])
                #print("yA:%.2f" % yA)
                xB = min(nbbox[0]+nbbox[2], cbbox[0]+cbbox[2])
                #print("xB:%.2f" % xB)
                yB = min(nbbox[1]+nbbox[3], cbbox[1]+cbbox[3])
                #print("yB:%.2f" % yB)
                              
                interArea = max(0, xB -xA + 1) * max(0, yB -yA + 1)
                #print("interArea:%.2f" % interArea)
                              
                boxNArea = (nbbox[2] + 1) * (nbbox[3] + 1) 
                boxCArea = (cbbox[2] + 1) * (cbbox[3] + 1)                                                
                # compute the intersection over union by taking the intersection
                # area and dividing it by the sum of prediction  ground-truth
                # areas - the interesection area
                iou = interArea / float(boxCArea + boxNArea - interArea)
                iou_temp.append(iou)

            if max(iou_temp) > 0:
                iou_array = np.array(iou_temp)
                index = np.argmax(iou_array)
                self.__IoU_predict_ids.append(self.__cur_ids[index])
                self.__IoU_predict_percentage.append(round(iou_temp[index]*100,2))
            else:
                self.__IoU_predict_ids.append('id_???')
                self.__IoU_predict_percentage.append(0)

        for i in range(len(self.__IoU_predict_ids)):
            next_frame_id = 'next frame index' + str(i) +': ' + self.__next_ids[i]
            if i < len(self.__cur_ids):
                predict_id = ' predict current frame ID: '+ self.__cur_ids[i] + ',' + str(self.__IoU_predict_percentage[i]) + "%"
            else:
                predict_id = ' not at the current frame'
            self.pym.PY_LOG(False, 'D', self.__class__, next_frame_id + predict_id)

    def read_amount_of_cur_frame_people(self):
        return len(self.__cur_ids)
    
    def read_amount_of_next_frame_people(self):
        return len(self.__next_ids)
    
    def next_frame_ids_list(self):
        return self.__next_ids

    def show_IoU_predict_ids_and_percentage(self):
        self.pym.PY_LOG(False, 'D', self.__class__, "show_IoU_predict_ids_and_percentage")
        id_val = ''
        percentage = 0
        for i in range(len(self.__IoU_predict_ids)):
            id_val = self.__IoU_predict_ids[i]
            percentage = self.__IoU_predict_percentage[i]
            self.pym.PY_LOG(False, 'D', self.__class__, "%s" % id_val + " ,%f" % percentage + '%')

    def use_SIFT_or_IoU_to_determine_id(self):
        self.__final_predict_ids = []
        print(self.__IoU_predict_ids)
        print(self.__SIFT_feature_match_ids)
        for i,SIFT_id in enumerate(self.__SIFT_feature_match_ids):
            if SIFT_id == self.__IoU_predict_ids[i]:
                # into this section which means both id prediction is the same
                self.__final_predict_ids.append(SIFT_id)
            elif self.__SIFT_feature_match_point[i] >= self.__SIFT_match_point_threshold:
                # use SIFT match method
                self.__final_predict_ids.append(SIFT_id)
            elif self.__IoU_predict_percentage[i] >= self.__IoU_match_threshold:
                # use IoU match
                self.__final_predict_ids.append(self.__IoU_predict_ids[i])
            else:
                self.__final_predict_ids.append('id_???')

    def show_final_predict_ids(self):
        for i,id_val in enumerate(self.__final_predict_ids):
            self.pym.PY_LOG(False, 'D', self.__class__,  "final_predict_id:%s" % id_val)
        

    def read_final_predict_ids(self, index):
        return self.__final_predict_ids[index]

    def init_for_next_round(self):

        # remove temp png
        ct = 0;
        while True:
            path = self.__combine_table_path + str(ct) + '.png'
            if os.path.isfile(path):
                os.remove(path)
            else:
                break
            ct += 1

        self.__cur_crop_objects = []
        self.__cur_crop_objects_12_unit = []
        self.__cur_crop_objects_12_unit_wb = []
        self.__next_crop_objects = []
        self.__next_crop_objects_12_unit = []
        self.__next_crop_objects_12_unit_wb = []
        self.__cur_ids = []
        self.__cur_ids_12_unit = []
        self.__next_ids = []
        self.__next_ids_12_unit = []
        self.__cur_bboxes = []
        self.__next_bboxes = []
        self.__cur_timestamp = ''
        self.__next_timestamp = ''
        self.__cur_destors = []
        self.__next_destors = []
        self.__cur_ids_img_table = []
        self.__cur_no_ids_img_table = []
        self.__next_ids_img_table = []
        self.__next_no_ids_img_table = []
        self.__bbox_colors = []
        self.__combine_table = []
        self.__SIFT_feature_match_point = []
        self.__SIFT_feature_match_ids = []
        self.__IoU_predict_ids = []
        self.__IoU_predict_percentage = []
        self.__final_predict_ids = []

