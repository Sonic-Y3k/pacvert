#  This file is part of Pacvert.

from os import path, stat, walk, remove
from time import time
from operator import itemgetter

import pacvert
import logger
from pymediainfo import MediaInfo
from helpers import fullpathToPath, fullpathToExtension, sortQueue
import pacvert.config
import helpers
from pacvert.converter import Converter
from pacvert.converter_ffmpeg import FFMpegError, FFMpegConvertError

def scan():
    """
    Scan given directory for new files.
    """
    #print(pacvert.CONFIG.SCAN_DIRECTORIES_PATH)
    for root,dirnames,filenames in walk(pacvert.CONFIG.SCAN_DIRECTORIES_PATH):
        for filename in filenames:
            if not is_file_ignored(path.join(root,filename)):
                add_file_to_queue(path.join(root,filename))

def add_file_to_queue(inputfile):
    """
    Add file to working queue.
    """
    
    if path.isfile(inputfile) \
        and has_file_valid_extension(inputfile) \
        and is_file_old_enough(inputfile) \
        and not is_file_in_output_dir(inputfile) \
        and not is_file_in_queue(inputfile):
        newfile = ScannedFile(inputfile)

        if len(newfile.mediainfo.tracks) > 1:
            logger.info("New file: '"+inputfile+"'")
            pacvert.WORKING_QUEUE.append(newfile)
            pacvert.IGNORE_QUEUE.append(inputfile)
        else:
            logger.debug("File '"+inputfile+"' doesn't have any tracks. It will be ignored.")
            pacvert.IGNORE_QUEUE.append(inputfile)
    elif not path.isfile(inputfile):
        logger.error("File '"+inputfile+"' doesn't exist.")

def is_file_in_output_dir(inputfile):
    """
    Check if a given file is already in our output directory.
    """
    if fullpathToPath(inputfile) == pacvert.CONFIG.OUTPUT_DIRECTORY:
        logger.debug("File '"+inputfile+"' is in our output directory. It will be ignored.")
        pacvert.IGNORE_QUEUE.append(inputfile)
        return True
    else:
        return False

def is_file_ignored(inputfile):
    """
    Check if we have already decided to defnitly not use that file.
    """
    if any(x == inputfile for x in pacvert.IGNORE_QUEUE):
        return True
    else:
        return False

def is_file_in_queue(inputfile):
    """
    Check if a given file (by it's full path) exists in the working queue.
    
    Return: "True" if file exists
    Otherwise: "False".
    """
    if any(x.fullpath == inputfile for x in pacvert.WORKING_QUEUE):
        logger.debug("File '"+inputfile+"' already in working queue.")
        return True
    else:
        logger.debug("File '"+inputfile+"' not in working queue.")
        return False

def is_file_old_enough(inputfile, t=30):
    """
    Check if a given file (by it's full path) was last modified a certain time period
    (Default: 30s) ago.
    """
    timedifference = round(time() - path.getmtime(inputfile))
    logger.debug("File '"+inputfile+"' was last modified "+str(timedifference)+"s ago (Limit: "+str(t)+"s).")
    if t < timedifference:
        return True
    else:
        return False

def has_file_valid_extension(inputfile):
    """
    Check if a given file (by it's full path) has a valid file extension
    """
    if fullpathToExtension(inputfile) in pacvert.CONFIG.SEARCH_FILE_FORMATS:
        logger.debug("File '"+inputfile+"' has a valid extension ("+fullpathToExtension(inputfile)+").")
        return True
    else:
        logger.debug("File '"+inputfile+"' has a invalid extension ("+fullpathToExtension(inputfile)+"). It will be ignored.")
        pacvert.IGNORE_QUEUE.append(inputfile)
        return False

class ScannedFile:
    """
    Object that stores the path and mediainfo of file.
    """
    added = None
    finished = None
    fullpath = None
    mediainfo = None
    crop = None

    """
    Status variable:
      0: active
      1: scanned
      2: pending
      3: finished
      4: error
    """
    status = 1
    progress = 0.0
    def __init__(self, fpath):
        try:
            self.added = helpers.now()
            self.finished = -1
            self.fullpath = fpath
            self.mediainfo = MediaInfo.parse(self.fullpath)
            self.updateStatus(2)
            self.createThumbs()
            self.crop = self.analyzeThumbs()
            self.deleteThumbs()
        except Exception as e:
            logger.error(e)

    def createThumbs(self):
        """
        Create thumbnails for crop-rectangle analysis
        """
        c = Converter()
        try:
            frame_count = helpers.getFrameCountFromMediainfo(self.mediainfo)
            if frame_count == -1:
                logger.error("We got a negative frame count from mediainfo.")
                raise ValueError("We got a negative frame count from mediainfo.")
            frame_rate = helpers.getFrameRateFromMediaInfo(self.mediainfo)
            
            chunks = helpers.genChunks(frame_count,10)
            
            filedirectory = helpers.fullpathToPath(self.fullpath)
            
            for i in range(10):
                logger.debug("Creating thumb #"+str(i)+" for "+self.fullpath)
                c.thumbnail(self.fullpath,helpers.cast_to_int(chunks[i]/frame_rate),filedirectory+'/'+str(i)+'.jpg', None, 5)
        except Exception as e:
            logger.error("ffmpeg: " +e.message + " with command: "+ e.cmd)


    def analyzeThumbs(self):
        """
        """
        c = Converter()
        return c.cropAnalysis(helpers.fullpathToPath(self.fullpath))

    def deleteThumbs(self):
        """
        """
        try:
            for i in range(10):
                remove(helpers.fullpathToPath(self.fullpath)+'/'+str(i)+'.jpg')
        except IOError:
            logger.error("One or more thumbs are not available and therefor cant be deleted.")

    def updateStatus(self, newVal):
        """
        Update status of scanned file and resort the queue.
        """
        logger.debug("Setting "+self.fullpath+" from status "+helpers.statusToString(self.status).lower()+" to "+helpers.statusToString(newVal).lower())
        self.status = newVal
        helpers.sortQueue()
    
    def getAsDict(self):
        """
        Returns Object as dict
        """
        dictR = {}
        dictR['added'] = self.added
        dictR['finished'] = self.finished
        dictR['fullpath'] = self.fullpath
        dictR['status'] = self.status
        dictR['progress'] = self.progress
        return dictR
