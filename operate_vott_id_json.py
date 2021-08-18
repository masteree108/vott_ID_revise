import os
import json
import enum
import log as PYM

class BBOX_ITEM(enum.Enum):
    height = 0
    width = 1
    left = 2
    top = 3

class VIDEO_SIZE(enum.Enum):
    W = 0
    H = 1

class operate_vott_id_json():
# private
    __log_name = '< class operate_vott_id_json>'
    __asset_id = ''
    __asset_format = ''
    __asset_name = ''
    __asset_path = ''

    #default
    __video_size = [3840, 2160]

    __parent_id = ''
    __parent_name = ''

    __timestamp = 0.01
    __tags = []
    __boundingBox = []
    __object_num = 0
    __ids = []
    __file_path = ''
    __compare_state = ' '
    __id_changed = 'N'

    def __print_read_parameter_from_json(self, num):
        self.pym.PY_LOG(False, 'D', self.__log_name, 'asset_id: %s' % self.__asset_id)
        self.pym.PY_LOG(False, 'D', self.__log_name, 'asset_format: %s' % self.__asset_format)
        self.pym.PY_LOG(False, 'D', self.__log_name, 'asset_name: %s' % self.__asset_name)
        self.pym.PY_LOG(False, 'D', self.__log_name, 'asset_path: %s' % self.__asset_path)
        self.pym.PY_LOG(False, 'D', self.__log_name, 'video_width: %d' % self.__video_size[VIDEO_SIZE.W.value])
        self.pym.PY_LOG(False, 'D', self.__log_name, 'video_height: %d' % self.__video_size[VIDEO_SIZE.H.value])

        self.pym.PY_LOG(False, 'D', self.__log_name, 'parent_id: %s' % self.__parent_id)
        self.pym.PY_LOG(False, 'D', self.__log_name, 'parent_name: %s' % self.__parent_name)
        self.pym.PY_LOG(False, 'D', self.__log_name, 'parent_path: %s' % self.__parent_path)

        self.pym.PY_LOG(False, 'D', self.__log_name, 'timestamp: %.5f' % self.__timestamp)
        for i in range(num):
            self.pym.PY_LOG(False, 'D', self.__log_name, 'tags[%d]:' % i + '%s' % self.__tags[i])
            self.pym.PY_LOG(False, 'D', self.__log_name, 'bounding box height[%d]:'% i + '%s' % self.__boundingBox[i][BBOX_ITEM.height.value])
            self.pym.PY_LOG(False, 'D', self.__log_name, 'bounding box width[%d]:'% i + '%s' % self.__boundingBox[i][BBOX_ITEM.width.value])
            self.pym.PY_LOG(False, 'D', self.__log_name, 'bounding box left[%d]:'% i + '%s' % self.__boundingBox[i][BBOX_ITEM.left.value])
            self.pym.PY_LOG(False, 'D', self.__log_name, 'bounding box top[%d]:'% i + '%s' % self.__boundingBox[i][BBOX_ITEM.top.value])
    
    def __read_id_from_tags(self):
        self.pym.PY_LOG(False, 'D', self.__log_name, 'name:%s' % self.__asset_name)
        self.__ids = []
        for i, tags in enumerate(self.__tags):
            for num in range(len(tags)):
                if tags[num][:3] == 'id_':
                    self.__ids.append(tags[num])
                    break

    def __read_data_from_id_json_file(self):
        try:
            with open(self.__file_path, 'r') as reader:
                self.pym.PY_LOG(False, 'D', self.__log_name, '%s open ok!' % self.__file_path)
                jf = json.loads(reader.read())

                self.__asset_id = jf['asset']['id']
                self.__asset_format = jf['asset']['format']
                self.__asset_name = jf['asset']['name']
                self.__asset_path = jf['asset']['path']
                video_width = jf['asset']['size']['width']
                video_height = jf['asset']['size']['height']
                self.__video_size[VIDEO_SIZE.W.value] = video_width
                self.__video_size[VIDEO_SIZE.H.value] = video_height
                self.__timestamp = jf['asset']['timestamp']

                self.__parent_id = jf['asset']['parent']['id']
                self.__parent_name = jf['asset']['parent']['name']
                self.__parent_path = jf['asset']['parent']['path']

                # using length of region to judge how many objects in this frame
                self.__object_num = len(jf['regions'])

                # must init list before using it, otherwise other class will connect to this list(maybe it's python bug)
                self.__tags = []
                self.__boundingBox = []
                for i in range(self.__object_num):
                    self.__tags.append([])
                    for j in range(len(jf['regions'][i]['tags'])):
                        self.__tags[i].append(jf['regions'][i]['tags'][j])

                    self.__boundingBox.append([])
                    h = jf['regions'][i]['boundingBox']["height"]
                    w = jf['regions'][i]['boundingBox']["width"]
                    l = jf['regions'][i]['boundingBox']["left"]
                    t = jf['regions'][i]['boundingBox']["top"]
                    
                    # if the bbox is exceeds the range of frame, just do below things
                    if l <= 0:
                        l = 0
                        self.pym.PY_LOG(False, 'D', self.__log_name, 'left:%s' % str(l))

                    if t <= 0:
                        t = 0 
                        self.pym.PY_LOG(False, 'D', self.__log_name, 'top:%s' % str(t))

                    if l+w > video_width:
                        w = video_width - l
                        self.pym.PY_LOG(False, 'D', self.__log_name, 'width:%s' % str(w))

                    if t+h > video_height:
                        h = video_height - t
                        self.pym.PY_LOG(False, 'D', self.__log_name, 'height:%s' % str(h))

                    self.__boundingBox[i].append(h)
                    self.__boundingBox[i].append(w)
                    self.__boundingBox[i].append(l)
                    self.__boundingBox[i].append(t)

                self.pym.PY_LOG(False, 'D', self.__log_name, '%s read ok!' % self.__file_path)
                reader.close()

                self.__print_read_parameter_from_json(self.__object_num)
                self.__read_id_from_tags()
            return 0
        except:
            reader.close()
            self.pym.PY_LOG(False, 'E', self.__log_name, '%s has wrong format!' % self.__file_path)
            return -1

# public
    def __init__(self):
        # below(True) = exports log.txt
        self.pym = PYM.LOG(True)
        
    def __del__(self):
        #deconstructor
        self.shut_down_log("over")


    def write_data_to_id_json_file(self, new_id_list):
        try:
            with open(self.__file_path, 'r') as f:
                self.pym.PY_LOG(False, 'D', self.__log_name, '%s open ok!' % self.__file_path)
                jf = json.load(f)
                self.pym.PY_LOG(False, 'D', self.__log_name, 'object_num:%s' % self.__object_num)
                for i in range(self.__object_num):
                    for j in range(len(jf['regions'][i]['tags'])):
                        id_val = jf['regions'][i]['tags'][j]
                        if id_val.find('id_', 0, 3)!=-1:
                            jf['regions'][i]['tags'][j] = new_id_list[i]

                self.pym.PY_LOG(False, 'D', self.__log_name, '%s modify ok!' % self.__file_path)
                f.close()

            with open(self.__file_path, 'w') as f:
                json.dump(jf, f, indent = 4)
                self.set_id_changed_to_Y()
                f.close()

            return 0
        except:
            f.close()
            self.pym.PY_LOG(False, 'E', self.__log_name, '%s has wrong format!' % self.__file_path)
            return -1


    def check_file_exist(self):
        if os.path.exists(self.__file_path):
            self.pym.PY_LOG(False, 'D', self.__log_name, '%s existed!' % self.__file_path)
            return True
        else:
            self.pym.PY_LOG(True, 'E', self.__log_name, '%s is not existed!' % self.__file_path)
            return False

    def read_all_file_info(self, path, all_data_list):
        self.__file_path = path + all_data_list
        self.pym.PY_LOG(False, 'D', self.__log_name, 'file_path:%s' % self.__file_path)
        return self.__read_data_from_id_json_file()

    def get_asset_id(self):
        return self.__asset_id
    
    def get_asset_format(self):
        return self.__asset_format
    
    def get_asset_name(self):
        return self.__asset_name

    def get_asset_path(self):
        return self.__asset_path

    def get_parent_id(self):
        return self.__parent_id
    
    def get_parent_name(self):
        return self.__parent_name
    
    def get_parent_path(self):
        return self.__parent_path

    def get_video_size(self):
        return self.__video_size

    def get_timestamp(self):
        return self.__timestamp
    
    def get_tags(self):
        return self.__tags

    def get_boundingBox(self):
        bbox = [] 
        for i in range(self.__object_num):
            bbox.append(())
            bbox[i] = (self.__boundingBox[i][BBOX_ITEM.left.value]     #x1=left
                        , self.__boundingBox[i][BBOX_ITEM.top.value]     #y1=top    
                        , self.__boundingBox[i][BBOX_ITEM.width.value]     #x2=width    
                        , self.__boundingBox[i][BBOX_ITEM.height.value]     #y2=height
                        )
        return bbox

    def shut_down_log(self, msg):
        self.pym.PY_LOG(True, 'D', self.__log_name, msg)

    
    def get_object_number(self):
        return self.__object_num

    def get_ids(self):
        return self.__ids
    
    def update_ids(self, new_id_list):
        self.__ids = []
        self.__ids = new_id_list.copy()

    def set_compare_state(self, state):
        if state == 0:
            self.__compare_state = 'current_frame'
        else:
            self.__compare_state = 'next_frame'
        
    def get_compare_state(self):
        return self.__compare_state

    def set_id_changed_to_Y(self):
        self.__id_changed = 'Y'

    def get_id_changed(self):
        return self.__id_changed
