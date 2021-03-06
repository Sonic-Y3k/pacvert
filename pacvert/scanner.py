#  This file is part of Pacvert.

from os import path, stat, walk, remove, rename
from time import time
from operator import itemgetter

import pacvert
import logger
from pymediainfo import MediaInfo
import helpers
from helpers import now, fullpathToPath, fullpathToExtension, statusToString, generateOutputFilename, getNewFileID
import pacvert.config
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

        if len(newfile.mediainfo) >= 1:
            logger.info("New file: '"+inputfile+"'")
            pacvert.thequeue.addPending(newfile)
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
    if pacvert.CONFIG.OUTPUT_DIRECTORY in fullpathToPath(inputfile):
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
    if any(x.fullpath == inputfile for x in pacvert.thequeue.getMerged(-1)):
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
    fileid = None
    added = None
    finished = None
    fullpath = None
    outputfilename = None
    mediainfo = None
    crop = None
    rename = None
    timestarted = 0

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
            self.added = now()
            self.finished = 0
            self.fullpath = fpath
            self.fileid = getNewFileID()
            tempMediainfo = MediaInfo.parse(self.fullpath)
            self.mediainfo = {}
            for track in tempMediainfo.tracks:
                if track.track_type not in self.mediainfo:
                    self.mediainfo[track.track_type] = track.to_data()
                else:
                    if track.track_type in ['Audio', 'Subtitle']:
                        if not isinstance(self.mediainfo[track.track_type], list):
                            tempTrack = self.mediainfo[track.track_type]
                            self.mediainfo[track.track_type] = []
                            self.mediainfo[track.track_type].append(tempTrack)
                        
                        self.mediainfo[track.track_type].append(track.to_data())
            
            self.outputfilename = pacvert.CONFIG.OUTPUT_DIRECTORY+'/'+generateOutputFilename(self.fullpath)
            self.createThumbs()
            self.crop = self.analyzeThumbs()
            self.deleteThumbs()
            self.updateStatus(2)
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
        
        # set status of element.
        self.status = newVal
        
        
        if newVal == 0: # active
            self.timestarted = now()
        elif newVal == 3: # finished
            self.deleteOriginal() # delete original if successful transcoded and file deletion is enabled.
            self.performRename() # rename file if file was renamed via webinterface

    def setRename(self, newName):
        """
        """
        logger.info("Rename "+self.fullpath+" to "+newName)
        self.rename = newName
    
    def performRename(self):
        """
        """
        if (self.rename is not None) and (self.status == 3):
            try:
                rename(self.outputfilename, pacvert.CONFIG.OUTPUT_DIRECTORY+'/'+generateOutputFilename(self.rename))
                logger.debug("Renaming file \'"+self.fullpath+"\' to \'"+self.rename+"\' was successful.")
            except IOError:
                logger.error("Renaming file \'"+self.fullpath+"\' to \'"+self.rename+"\' failed.")
    
    def getAsDict(self):
        """
        Returns Object as dict
        """
        dictR = {}
        dictR['id'] = self.fileid
        dictR['added'] = self.added
        dictR['finished'] = self.finished
        dictR['rename'] = self.rename
        dictR['fullpath'] = self.fullpath
        dictR['mediainfo'] = { # just add neccessary things, keep the traffic low
            'General': {
                'format': self.mediainfo['General']['format'],
                'file_size': self.mediainfo['General']['file_size']
            },
            'Video': {
                'frame_count': self.mediainfo['Video']['frame_count']
            }
        }
        dictR['status'] = statusToString(self.status)
        dictR['progress'] = self.progress
        dictR['timestarted'] = self.timestarted
        return dictR
    
    def deleteOriginal(self):
        """
        Delete the original file. Should be used after successfully finnishing a file.
        """
        try:
            logger.debug("Deleting file \'"+self.fullpath+"\'")
            remove(self.fullpath)
        except IOError:
            logger.error("Deleting file \'"+self.fullpath+"\' failed.")
