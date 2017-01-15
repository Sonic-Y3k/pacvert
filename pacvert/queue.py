#  This file is part of Pacvert.

import pacvert
import logger
from operator import attrgetter
from helpers import now
from threading import RLock
from inspect import currentframe, getouterframes

class ElementQueue:
    active = []
    pending = []
    failed = []
    finished = []
    lock = None
    
    def get_caller(self):
        return getouterframes(currentframe())[1][3]
    
    def __init__(self):
        """
        """
        self.lock = RLock()
    
    def get(self, cls_cat):
        """
        """
        return getattr(self, cls_cat)
    
    def get_all(self, status_filter=-1):
        """
        """
        if status_filter < 0:
            return self.get('active')+self.get('pending')+self.get('failed')+self.get('finished')
        elif status_filter == 0:
            return self.get('active')
        elif status_filter == 2:
            return self.get('pending')
        elif status_filter == 3:
            return self.get('finished')
        else:
            return self.get('failed')
    
    def pop(self, cls_cat):
        """
        """
        tempResult = []
        with self.lock:
            return self.get(cls_cat).pop(0)

        return tempResult
    
    def remove(self, cls_id):
        """
        """
        with self.lock:
            for cat in ['pending', 'finished', 'error']:    
                for elem in self.get(cat):
                    if elem.unique_id == cls_id:
                        self.get(cat).remove(elem)
    
    def move(self, cls_id, direction):
        """
        """
        current_position = -1
        with self.lock:
            for cat in ['pending', 'finished', 'error']:
                current_position = self.get_index_from_unique_id(cat, cls_id)
                if current_position >= 0:
                    new_index = current_position + direction
                    if new_index <= self.len(cat) and new_index >= 0:
                        self.get(cat)[current_position], self.get(cat)[new_index] = self.get(cat)[new_index], self.get(cat)[current_position]
                
    def append(self, cls_cat, obj):
        """
        """
        with self.lock:
            if cls_cat == 'active':
                obj.status_set_status(0)
                obj.status_set_start(now())
                self.active.append(obj)
            elif cls_cat == 'pending':
                obj.status_set_status(2)
                self.pending.append(obj)
            elif cls_cat == 'finished':
                obj.status_set_status(3)
                obj.status_set_finished(now())
                obj.perform_rename()
                obj.delete_original()
                self.finished.append(obj)
            else:
                obj.status_set_status(4)
                obj.status_set_finished(now())
                obj.delete_transcode()
                self.failed.append(obj)
            logger.debug(obj.file_name+obj.file_extension+' is set to '+cls_cat)

    def len(self, cls_cat):
        return len(self.get(cls_cat))
    
    def get_index_from_unique_id(self, cls_cat, obj_id):
        try:
            for i in self.get(cls_cat):
                if i.unique_id == obj_id:
                    return self.get(cls_cat).index(i)
        except ValueError:
            return -1
        return -1