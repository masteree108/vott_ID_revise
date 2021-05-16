import os
import sys
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

class read_vott_id_json():
# private
    __log_name = '< class read_vott_id_json>'
    __asset_id = ''
    __asset_format = ''
    __asset_name = ''
    __asset_path = ''
    __video_size = [3840, 2160]

    __parent_id = ''
    __parent_name = ''

    __timestamp = 0.01
    __tags = []
    __boundingBox = []
    __object_num = 0
    __ids = []
    __file_path = ''

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
        state_table = ['ok', 'no_id', 'same_id']
        for i, tags in enumerate(self.__tags):
            for num in range(len(tags)):
                if tags[num][:3] == 'id_':
                    self.__ids.append(tags[num])
                    break
        # no ID check
        if len(self.__ids) != len(self.__tags):
            self.pym.PY_LOG(True, 'E', self.__log_name, 'There are no ID')
            return False, state_table[1]
             
        # ID duplicate check
        if len(self.__ids) != len(set(self.__ids)):
            self.pym.PY_LOG(True, 'E', self.__log_name, 'duplicated ID')
            return False, state_table[2]
             
        self.pym.PY_LOG(False, 'D', self.__log_name, 'get ids: %s' % self.__ids)
        return True, state_table[0]

# public
    def __init__(self, file_path):
        # below(True) = exports log.txt
        self.pym = PYM.LOG(True)
        self.__file_path = file_path
        
    #del __del__(self):
        #deconstructor 

    def check_file_exist(self):
        if os.path.exists(self.__file_path):
            self.pym.PY_LOG(False, 'D', self.__log_name, '%s existed!' % self.__file_path)
            return True
        else:
            self.pym.PY_LOG(True, 'E', self.__log_name, '%s is not existed!' % self.__file_path)
            return False


    def read_data_from_id_json_data(self):
        try:
            with open(self.__file_path, 'r') as reader:
                self.pym.PY_LOG(False, 'D', self.__log_name, '%s open ok!' % self.__file_path)
                jf = json.loads(reader.read())

                self.__asset_id = jf['asset']['id']
                self.__asset_format = jf['asset']['format']
                self.__asset_name = jf['asset']['name']
                self.__asset_path = jf['asset']['path']
                self.__video_size[VIDEO_SIZE.W.value] = jf['asset']['size']['width']
                self.__video_size[VIDEO_SIZE.H.value] = jf['asset']['size']['height']
                self.__timestamp = jf['asset']['timestamp']

                self.__parent_id = jf['asset']['parent']['id']
                self.__parent_name = jf['asset']['parent']['name']
                self.__parent_path = jf['asset']['parent']['path']

                # using length of region to judge how many objects in this frame
                self.__object_num = len(jf['regions'])
                for i in range(self.__object_num):
                    self.__tags.append([])
                    for j in range(len(jf['regions'][i]['tags'])):
                        self.__tags[i].append(jf['regions'][i]['tags'][j])

                    self.__boundingBox.append([])
                    self.__boundingBox[i].append(jf['regions'][i]['boundingBox']["height"])
                    self.__boundingBox[i].append(jf['regions'][i]['boundingBox']["width"])
                    self.__boundingBox[i].append(jf['regions'][i]['boundingBox']["left"])
                    self.__boundingBox[i].append(jf['regions'][i]['boundingBox']["top"])

                self.pym.PY_LOG(False, 'D', self.__log_name, '%s read ok!' % self.__file_path)
                reader.close()

                self.__print_read_parameter_from_json(self.__object_num)

                return self.__read_id_from_tags()
        except:
            self.pym.PY_LOG(False, 'E', self.__log_name, '%s has wrong format!' % self.__file_path)
            sys.exit()

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
