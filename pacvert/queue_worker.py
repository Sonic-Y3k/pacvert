#  This file is part of Pacvert.

import pacvert
import logger
import threading
import time

from pacvert.converter import Converter
from pacvert.converter_ffmpeg import FFMpegError, FFMpegConvertError
c = Converter()

def start_thread():
    # Start the websocket listener on it's own thread
    threading.Thread(target=run).start()

def run():
    """
    Scan given directory for new files.
    """
    while True:
        if len(pacvert.WORKING_QUEUE) > 0 and not pacvert.WORKING_QUEUE[0].processing:
            pacvert.WORKING_QUEUE[0].processing = True
            try:
                conv = c.convert(pacvert.WORKING_QUEUE[0].fullpath, '/tmp/output.mkv',
                {
                    'format': 'mkv',
                    'video': {
                       'codec': pacvert.DEFAULT_CODEC_VIDEO,
                        'width': 720,
                        'height': 400,
                        'fps': 1,
                    },
                    'audio': {
                        'codec': pacvert.DEFAULT_CODEC_AUDIO,
                    }
                })
                for timecode in conv:
                    logger.debug("Converting ("+str(timecode)+")...")
                pacvert.WORKING_QUEUE.pop(0)
                logger.debug("Finished File")
            except FFMpegConvertError as e:
                logger.error("ffmpeg: " +e.message + " with command: "+ e.cmd)
            time.sleep(1)

