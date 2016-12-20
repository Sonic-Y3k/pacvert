#  This file is part of pacvert

'''
Created on Aug 1, 2011

@author: Michael
'''
import platform

from pacvert import version

# Identify Our Application
USER_AGENT = 'PlexPy/-' + version.PACVERT_VERSION + ' v' + version.PACVERT_RELEASE_VERSION + ' (' + platform.system() + \
             ' ' + platform.release() + ')'

PLATFORM = platform.system()
PLATFORM_VERSION = platform.release()
BRANCH = version.PACVERT_VERSION
VERSION_NUMBER = version.PACVERT_RELEASE_VERSION

# Notification Types
NOTIFY_STARTED = 1
NOTIFY_STOPPED = 2

notify_strings = {}
notify_strings[NOTIFY_STARTED] = "Playback started"
notify_strings[NOTIFY_STOPPED] = "Playback stopped"

DEFAULT_USER_THUMB = "interfaces/default/images/gravatar-default-80x80.png"
DEFAULT_POSTER_THUMB = "interfaces/default/images/poster.png"
DEFAULT_COVER_THUMB = "interfaces/default/images/cover.png"

PLATFORM_NAME_OVERRIDES = {'Konvergo': 'Plex Media Player',
                           'Mystery 3': 'Playstation 3',
                           'Mystery 4': 'Playstation 4',
                           'Mystery 5': 'Xbox 360'}

MEDIA_FLAGS_AUDIO = {'ac.?3': 'dolby_digital',
                     'truehd': 'dolby_truehd',
                     '(dca|dta)': 'dts',
                     'dts(hd_|-hd|-)?ma': 'dca-ma',
                     'vorbis': 'ogg'
                     }
MEDIA_FLAGS_VIDEO = {'avc1': 'h264',
                     'wmv(1|2)': 'wmv',
                     'wmv3': 'wmvhd'
                     }
