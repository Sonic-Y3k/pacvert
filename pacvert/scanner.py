#  This file is part of Pacvert.

from os import path, walk

import pacvert
import logger
from queue_element import QueueElement
from pymediainfo import MediaInfo

def scan():
    """
    Scan given directory for new files.
    """
    try:
<<<<<<< HEAD
        with pacvert.SCAN_LOCK:
            for root, directories, filenames in walk(pacvert.CONFIG.SCAN_DIRECTORIES_PATH):
                for filename in sorted(filenames):
                    full_path = path.join(root,filename)
                    if full_path not in pacvert.IGNORE_QUEUE:
                        logger.info('scanning \''+full_path+'\'')
                        test_file = QueueElement(full_path)
                        if (test_file.file_valid):
                            pacvert.IGNORE_QUEUE.append(full_path)
                            test_file.set_mediainfo(pullMediainfo(full_path))
                            test_file.file_configure()
                        
                            with pacvert.QUEUE_LOCK:    
                                pacvert.QUEUE.append('pending', test_file)
=======
        for root, directories, filenames in walk(pacvert.CONFIG.SCAN_DIRECTORIES_PATH):
            for filename in sorted(filenames):
                full_path = path.join(root,filename)
                
                if full_path not in pacvert.IGNORE_QUEUE and path.splitext(full_path)[1] in pacvert.CONFIG.SEARCH_FILE_FORMATS:
                    test_file = QueueElement(full_path)
                    
                    if test_file.file_validity() and test_file.file_configure():
                        pacvert.IGNORE_QUEUE.append(full_path)
                        pacvert.QUEUE.append('pending', test_file)
                    else:
                        logger.error('can\' add '+full_path+' to queue. Probably to young.')
>>>>>>> 749771c3516a58c8e2564ab13075d5cc5e7f40b4
    except Exception as e:
        logger.error('scanning directory \''+pacvert.CONFIG.SCAN_DIRECTORIES_PATH+'\' failed with: '+e.message)
        
def pullMediainfo(filename):
    """
    """
    try:
        logger.debug("  starting to pull mediainfo from "+filename)
        tempMediainfo = MediaInfo.parse(filename) # try to parse mediainfo from file
        result = {}
        
        for track in tempMediainfo.tracks:
            if track.track_type == 'General':
                result['General'] = track.to_data()
            elif track.track_type == 'Video' and 'Video' not in result:
                result['Video'] = track.to_data()
            elif track.track_type == 'Video' and 'Video' in result:
                if track.stram_size > result['Video']['stream_size']:
                    result['Video'] = track.to_data()
            elif track.track_type not in result and track.track_type not in ['Video', 'General']:
                result[track.track_type] = []
                result[track.track_type].append(track.to_data())
            else:
                result[track.track_type].append(track.to_data())
        return result
        #
    except Exception as e:
        return {}
        #logger.error("Getting mediainfo from '"+self.get_full_name_with_path()+"' failed with: "+e.strerror)