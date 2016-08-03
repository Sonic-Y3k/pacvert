#!/usr/bin/python2
from converter import Converter
c = Converter()

info = c.probe('/home/tschoenbach/Downloads/big_buck_bunny_480p_surround-fix.avi')

conv = c.convert('/home/tschoenbach/Downloads/big_buck_bunny_480p_surround-fix.avi', 
'/tmp/output.mkv', {
    'format': 'mkv',
    'audio': {
        'codec': 'mp3',
        'samplerate': 11025,
        'channels': 2
    },
    'video': {
        'codec': 'hevc',
        'width': 720,
        'height': 400,
        'fps': 30,
        'quality': 18.0,
        'pix_fmt': 'yuv420p10'
    }})

for timecode in conv:
    print("Converting (%f) ...\r" % timecode)
