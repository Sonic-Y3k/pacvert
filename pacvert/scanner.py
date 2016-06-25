#  This file is part of Pacvert.

from os import path, stat, walk
from time import time

import pacvert
import logger
from pymediainfo import MediaInfo
from helpers import human_duration, fullpathToExtension
import pacvert.config

def scan():
    """
    Scan given directory for new files.
    """
    #print(pacvert.CONFIG.SCAN_DIRECTORIES_PATH)
    for root,dirnames,filenames in walk(pacvert.CONFIG.SCAN_DIRECTORIES_PATH):
        for filename in filenames:
            add_file_to_queue(path.join(root,filename))

def add_file_to_queue(inputfile):
    """
    Add file to working queue.
    """
    
    if path.isfile(inputfile) \
        and not is_file_in_queue(inputfile) \
        and is_file_old_enough(inputfile) \
        and has_file_valid_extension(inputfile):
        logger.info("New file: '"+inputfile+"'")
        pacvert.WORKING_QUEUE.append(ScannedFile(inputfile))
    elif not path.isfile(inputfile):
        logger.error("File '"+inputfile+"' doesn't exist.")

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
        logger.debug("File '"+inputfile+"' has a invalid extension ("+fullpathToExtension(inputfile)+").")
        return False

class ScannedFile:
    """
    Object that stores the path and mediainfo of file.
    """
    fullpath = None
    mediainfo = None
    processed = None
    def __init__(self, fpath):
        self.fullpath = fpath
        self.mediainfo = MediaInfo.parse(self.fullpath)
        self.processed = False