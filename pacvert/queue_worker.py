#  This file is part of Pacvert.

import pacvert
import logger
import threading
import time

import pacvert.config
from pacvert.converter import Converter
from pacvert.converter_ffmpeg import FFMpegError, FFMpegConvertError
from pacvert.helpers import cast_to_int, generateOutputFilename, now

c = Converter()

def start_thread():
    # Start the websocket listener on it's own thread
    threading.Thread(target=run).start()

def run():
    """
    Scan given directory for new files.
    """
    while True:
        try:
            active = pacvert.thequeue.getActive()
            current = pacvert.thequeue.getPending()
            if (active == None) and (current != None):
                pacvert.thequeue.addActive(current)
                active = current

                try:
                    # setting up codec specific settings
                    video = {'codec': pacvert.CONFIG.DEFAULT_CODEC_VIDEO} # set the targets codec
                    if pacvert.CONFIG.DEFAULT_CODEC_VIDEO_CROP: # check if cropping is enabled
                        video['width'] = active.crop[0] # set width
                        video['height'] = active.crop[1] # set height
                        video['mode'] = 'crop' # set crop mode

                    if pacvert.CONFIG.DEFAULT_CODEC_VIDEO == "h264": # if target codec is h264
                        video['preset'] = pacvert.CONFIG.CODEC_AVC_PRESET # set preset
                        video['profile'] = pacvert.CONFIG.CODEC_AVC_PROFILE # set profile
                        video['quality'] = pacvert.CONFIG.CODEC_AVC_QUALITY # set quality
                        video['tune'] = pacvert.CONFIG.CODEC_AVC_TUNE # set tune
                        if pacvert.CONFIG.CODEC_AVC_AUTOMAXRATE: # if automatic maxrate is enabled
                            if pacvert.CONFIG.CODEC_AVC_BUFSIZE < 0 or pacvert.CONFIG.CODEC_H264_MAXRATE < 0:
                                if  'bit_rate' in active.mediainfo['Video']:
                                    video['maxrate'] = cast_to_int(active.mediainfo['Video']['bit_rate']) # set maxrate to video track bitrate
                                    video['bufsize'] = cast_to_int(active.mediainfo['Video']['bit_rate']*3) # set bufsize to three times the video bitrate
                            else:
                                video['maxrate'] = pacvert.CONFIG.CODEC_AVC_MAXRATE # set maxrate to given value
                                video['bufsize'] = pacvert.CONFIG.CODEC_AVC_BUFSIZE # set bufsize to given value
                        for anotheropt in pacvert.CONFIG.CODEC_AVC_ADDITIONALOPT: # if additional options are specified
                            video[anotheropt] = pacvert.CONFIG.CODEC_AVC_ADDITIONALOPT[anotheropt] # add options to out encoding list
                    elif pacvert.CONFIG.DEFAULT_CODEC_VIDEO == "hevc": # if target codec is hevc
                        video['preset'] = pacvert.CONFIG.CODEC_HEVC_PRESET # set preset
                        video['quality'] = pacvert.CONFIG.CODEC_HEVC_QUALITY # set quality
                        video['tune'] = pacvert.CONFIG.CODEC_HEVC_TUNE # set tune
                        if pacvert.CONFIG.CODEC_HEVC_AUTOMAXRATE: # set max rate
                            if pacvert.CONFIG.CODEC_HEVC_BUFSIZE < 0 or pacvert.CONFIG.CODEC_HEVC_MAXRATE < 0:
                                if  'bit_rate' in active.mediainfo['Video']:
                                    video['maxrate'] = cast_to_int(active.mediainfo['Video']['bit_rate']) # set maxrate to video track bitrate
                                    video['bufsize'] = cast_to_int(active.mediainfo['Video']['bit_rate']*3) # set bufsize to three times the video bitrate
                            else:
                                video['maxrate'] = pacvert.CONFIG.CODEC_HEVC_MAXRATE # set maxrate to given value
                                video['bufsize'] = pacvert.CONFIG.CODEC_HEVC_BUFSIZE # set bufsize to given value
                        for anotheropt in pacvert.CONFIG.CODEC_HEVC_ADDITIONALOPT: # if additional options are specified
                            video[anotheropt] = pacvert.CONFIG.CODEC_HEVC_ADDITIONALOPT[anotheropt] # add options to out encoding list
                    elif pacvert.CONFIG.DEFAULT_CODEC_VIDEO == "vp8": # if target codec is vp8
                        video['quality'] = pacvert.CONFIG.CODEC_VP8_QUALITY # set video quality
                        video['threads'] = pacvert.CONFIG.CODEC_VP8_THREADS # set no of real cores
                    else:
                        logger.error("Codec not yet implemented")

                    conv = c.convert(active.fullpath, active.outputfilename,
                    {
                        'format': 'mkv',
                        'video': video,
                        'audio': {
                            'codec': pacvert.CONFIG.DEFAULT_CODEC_AUDIO,
                        },
                        'subtitle': {
                            'codec': pacvert.CONFIG.DEFAULT_CODEC_SUBTITLE,
                        },
                        'map': 0,
                    })
                    for timecode in conv:
                        logger.debug("Converting ("+str(timecode)+")...")
                        active.progress = timecode
                    logger.info("Finished File: '"+active.fullpath+"'")
                    active.finished = now()
                    pacvert.thequeue.addFinished(pacvert.thequeue.getActive()) # set status to finished
                except FFMpegConvertError as e:
                    logger.error("ffmpeg: " +e.message + " with command: "+ e.cmd)

                    pacvert.thequeue.addFailed(pacvert.thequeue.getActive()) # set status to failed
                time.sleep(1)
        except Exception as e:
            logger.error(e)
