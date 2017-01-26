# This file is part of pacvert

# Global imports
from os import path, remove, rename
from time import time

# Project imports
import pacvert
import logger
from pymediainfo import MediaInfo
from helpers import cast_to_int, cast_to_float, genChunks, getNewFileID, now
from pacvert.converter import Converter
from converter_ffmpeg import FFMpegError, FFMpegConvertError

class QueueElement:
    """
    Queue Element
    """
    file_path = None        # Path to file
    file_name = None        # Filename without extension
    file_extension = None   # File extension
    file_size = None        # File size in bytes
    file_output = None      # Output
    file_output_size = 0    # Size of output file
    file_rename = None      # After transcode, rename.
    file_status_progress = 0.0
    file_status_status = 1
    file_status_crop = [0,0,0,0]
    file_status_added = now()
    file_status_start = 0
    file_status_finished = 0
    file_valid = False
    mediainfo = {}          # stores mediainfo informations
    unique_id = None        # unique id to identify a file queue independently

    def __init__(self, cls_filename):
        """ Constructor
        """
        self.file_path = path.dirname(cls_filename)
        self.file_name, self.file_extension = path.splitext(path.basename(cls_filename))
        self.file_size = path.getsize(cls_filename)
        logger.debug("creating new queue element '"+self.file_name+self.file_extension+"'")
        self.file_valid = self.file_validity()
    
    def file_configure(self):
        """ Configures object and sets required atributes
        """
        logger.debug('starting configuration of queue element \''+self.file_name+self.file_extension+'\'')
        self.file_output = self.get_new_name_with_path()
        self.unique_id = getNewFileID()
        
        try:
            if self.get_track_count_from_mediainfo('Video') == 1 and pacvert.CONFIG.DEFAULT_CODEC_VIDEO_CROP:
                self.analyze_crop()
        except Exception as e:
            logger.error(e.message)
                
        check_query = (self.get_track_count_from_mediainfo() > 0)
        if check_query:
            logger.debug('finished configuration of queue element \''+self.file_name+self.file_extension+'\' successfully')
        else:
            logger.error('failed configuration of queue element \''+self.file_name+self.file_extension+'\'')
        return check_query
        
    def set_mediainfo(self, cls_mediainfo):
        """
        """
        self.mediainfo = cls_mediainfo
        track_diff = str(self.get_track_count_from_mediainfo('Video'))+'v, ' \
                    +str(self.get_track_count_from_mediainfo('Audio'))+'a, ' \
                    +str(self.get_track_count_from_mediainfo('Subtitle')+self.get_track_count_from_mediainfo('Text'))+'s'
        logger.debug('  pulled '+str(self.get_track_count_from_mediainfo())+' ('+track_diff+') tracks.')
    
    def file_check_existance(self):
        """ Checks if file exists
        """
        check_query = (path.isfile(self.get_full_name_with_path()))
        if not check_query:
            logger.error(self.file_name+self.file_extension+' does not exist?!')
            pacvert.IGNORE_QUEUE.append(self.get_full_name_with_path())
        return check_query
            
    def file_check_time_modified(self, t=30):
        """ Checks if file was at least modified x seconds ago.
        
        Keyword arguments:
        t -- minimum seconds since last file modification
        """
        check_query = (abs(time() - path.getmtime(self.get_full_name_with_path())) > t)
        return check_query
    
    def file_check_extension(self):
        """ Checks for valid file extension
        """
        check_query = (self.file_extension in pacvert.CONFIG.SEARCH_FILE_FORMATS)
        if not check_query:
            logger.error(self.file_name+self.file_extension+' has a invalid extension.')
            pacvert.IGNORE_QUEUE.append(self.get_full_name_with_path())
        return check_query
        
    def file_check_directory(self):
        """ Checks if directory is not our output directory
        """
        check_query = (pacvert.CONFIG.OUTPUT_DIRECTORY not in self.file_path)
        if not check_query:
            logger.error(self.file_name+self.file_extension+' is in our output directory.')
            pacvert.IGNORE_QUEUE.append(self.get_full_name_with_path())
        return check_query
    
    def file_check_size(self, minimum=1048576):
        """ Checks if file is big enough
        
        Keyword arguments:
        minimum -- minimum filesize to compare with
        """
        check_query = (self.file_size > minimum)
        if not check_query:
            logger.error(self.file_name+self.file_extension+' is to small ('+self.file_size+' bytes)')
            pacvert.IGNORE_QUEUE.append(self.get_full_name_with_path())
        return check_query

    def file_validity(self):
        """ Checks if file is valid for us
        """
        logger.debug("checking validity of "+self.file_name+self.file_extension+"...")
        return (self.file_check_directory() \
                and self.file_check_existance() \
                and self.file_check_extension() \
                and self.file_check_size() \
                and self.file_check_time_modified())
    
    def output_rename(self, cls_newname):
        """ Set's a different name as output
        
        Keyword arguments:
        cls_newname -- the new name for the file
        """
        if self.file_status_status == 3: # file is finished, perform rename right now.
            if self.file_rename is not None:
                self.file_output = path.join(pacvert.CONFIG.OUTPUT_DIRECTORY, self.file_rename)
            
            self.file_rename = cls_newname
            self.perform_rename()
        else:
            self.file_rename = cls_newname
    
    def perform_rename(self):
        if path.exists(self.file_output) and self.file_rename is not None:
            try:
                fullpath_rename = pacvert.CONFIG.OUTPUT_DIRECTORY+'/'+self.file_rename
                
                if path.exists(pacvert.CONFIG.OUTPUT_DIRECTORY+'/'+self.file_rename):
                    split = path.splitext(self.file_rename)
                    rename(self.file_output, pacvert.CONFIG.OUTPUT_DIRECTORY+'/'+split[0]+'_'+now()+split[1])
                else:
                    rename(self.file_output, fullpath_rename)
            except IOError as e:
                logger.error('renaming file \''+self.file_output+'\' to \''++'\' failed with: '+e.message)
        elif not path.exists(self.file_output):
            logger.error('file to be renamed doesn\'t exist.')
    
    def get_full_name_with_path(self):
        """ Returns the full path, name and extension from this object
        """
        return self.file_path+"/"+self.file_name+self.file_extension
    
    def get_new_name_with_path(self):
        """ Returns the full path of the transcoded file before it's renamed
        """
        checkpath = pacvert.CONFIG.OUTPUT_DIRECTORY+'/'+self.file_name+self.file_extension
        if path.exists(checkpath):
            checkpath = pacvert.CONFIG.OUTPUT_DIRECTORY+'/'+self.file_name+'_'+now()+self.file_extension
        return checkpath
    
    def get_track_count_from_mediainfo(self, cls_track_type="all"):
        """ Returns the number of tracks per track_type
        """
        counter = 0
        try:
            if cls_track_type in self.mediainfo:                
                if cls_track_type == 'Video':
                    return 1
                elif cls_track_type in ['Audio', 'Subtitle', 'Text']:
                    return len(self.mediainfo[cls_track_type])
            elif cls_track_type == "all":
                for i in self.mediainfo:
                    counter += 1
            else:
                return 0
        except Exception as e:
            logger.error(e.message)
            return 0
        return counter
    
    def delete_original(self):
        """ Deletes the original file
        """
        try:
            logger.debug("Delete original file: '"+self.get_full_name_with_path()+"'")
            remove(self.get_full_name_with_path())
        except OSError as e:
            logger.error("Can't delete original file '"+self.get_full_name_with_path()+"'.")
    
    def delete_transcode(self):
        """ Deletes the transcoded file
        """
        try:
            logger.debug("Delete transcode-file: '"+self.file_output()+"'")
            remove(self.file_output())
        except (OSError, TypeError) as e:
            logger.error("Can't delete transcode for '"+self.get_full_name_with_path()+"'.")
        
    
    def analyze_crop(self):
        """ Run the different cropping functions
        """
        logger.debug("  creating thumbs for "+self.file_name+self.file_extension)
        try:
            self.create_thumbs()
            logger.debug("  finished creating thumbs. Starting analyzing cropping rectangle.")
            crop_rectangle = self.analyze_thumbs()
            logger.debug("  finished analyzing rectangle: "+str(crop_rectangle)+". Start deleting thumbs.")
            self.delete_thumbs()
            logger.debug("  finished deleting thumbs.")
            self.file_status_crop = crop_rectangle
        except FFMpegError:
            return [self.mediainfo['Video']['width'],self.mediainfo['Video']['height'],0,0]
        except Exception as e:
            logger.error("Failing to create cropping rectangle with following message: "+e.message)
            return [self.mediainfo['Video']['width'],self.mediainfo['Video']['height'],0,0]
        
    def create_thumbs(self):
        """ Create thumbnails for crop-rectangle analysis
        """
        c = Converter()
        
        frame_count = cast_to_int(self.mediainfo['Video']['frame_count'])
        frame_rate = cast_to_float(self.mediainfo['Video']['frame_rate'])
            
        chunks = genChunks(frame_count,10)
        
        for i in range(10):
            c.thumbnail(self.get_full_name_with_path(),cast_to_int(chunks[i]/frame_rate),pacvert.TEMP+'/'+str(i)+'.jpg', None, 5)
        
    def analyze_thumbs(self):
        """ Let ffmpeg analyze the cropping rectangle
        """
        c = Converter()
        try:
            return c.cropAnalysis(pacvert.TEMP) 
        except Exception as e:
            logger.error('  crop failed with: '+e.message)
        
        return [self.mediainfo['Video']['width'],self.mediainfo['Video']['height'],0,0]

    def delete_thumbs(self):
        """ Delete created jpegs
        """
        try:
            for i in range(10):
                remove(pacvert.TEMP+'/'+str(i)+'.jpg')
        except IOError:
            logger.error("One or more thumbs are not available and therefor cant be deleted.")
    
    def status_set_status(self, cls_new_status):
        """ updates status variable
        """
        self.file_status_status = cls_new_status
        
    def status_set_start(self, cls_new_start=now()):
        """ Set object start time to cls_new_start
        """
        self.file_status_start = cls_new_start
    
    def status_set_finished(self, cls_new_finished=now()):
        """ Set object finished time to cls_new_finished
        """
        self.file_status_finished = cls_new_finished
    
    def update_output_size(self):
        """ Returns the filesize of output
        """
        if path.exists(self.file_output):
            self.file_output_size = path.getsize(self.file_output)
        
    def export_object(self):
        """ Export our file into dict
        """
        return {
            'file_path': self.file_path,
            'file_name': self.file_name,
            'file_extension': self.file_extension,
            'file_size': self.file_size,
            'file_output': self.file_output,
            'file_rename': self.file_rename,
            'file_status_progress': self.file_status_progress,
            'file_status_status': self.file_status_status,
            'file_status_crop': self.file_status_crop,
            'file_status_added': self.file_status_added,
            'file_status_start': self.file_status_start,
            'file_status_finished': self.file_status_finished,
            'file_output_size': self.file_output_size,
            'mediainfo': self.mediainfo,
            'unique_id': self.unique_id
        }
        
    def get_track_ids(self):
        """ Returns a list of track ids
        """
        result_list = []
        
        for name, category in self.mediainfo.items():
            if name == 'Video':
                result_list.insert(0, int(category['streamorder']))
            elif name == 'Audio':
                for entry in category:
                    result_list.insert(1, int(entry['streamorder']))
            elif name in ['Subtitle', 'Text']:
                for entry in category:
                    result_list.append(int(entry['streamorder']))
        
        if len(result_list) == 0:
            return 0
            
        return result_list
        
    def import_object(self, cls_object_data):
        """ Import a dict and fill object accordingly
        
        Keyword arguments:
        cls_object_data -- a dict containing data
        """
        self.file_output = cls_object_data['file_output']
        self.file_output = cls_object_data['file_output']
        self.file_status = cls_object_data['file_status']
        self.mediainfo = cls_object_data['mediainfo']
        