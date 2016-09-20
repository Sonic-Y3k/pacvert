# This file is part of pacvert.

import arrow
import os
import re
import shutil

from configobj import ConfigObj

import pacvert
import logger


def bool_int(value):
    """
    Casts a config value into a 0 or 1
    """
    if isinstance(value, basestring):
        if value.lower() in ('', '0', 'false', 'f', 'no', 'n', 'off'):
            value = 0
    return int(bool(value))

FILENAME = "config.ini"

_CONFIG_DEFINITIONS = {
    'BACKUP_DIR': (str, 'General', ''),
    'CHECK_GITHUB': (int, 'General', 1),
    'CHECK_GITHUB_INTERVAL': (int, 'General', 360),
    'CHECK_GITHUB_ON_STARTUP': (int, 'General', 1),
    'CODEC_H264_ADDITIONALOPT': (list, 'CodecSettings', []),
    'CODEC_H264_AUTOMAXRATE': (bool, 'CodecSettings', True),
    'CODEC_H264_BUFSIZE': (int, 'CodecSettings', -1),
    'CODEC_H264_MAXRATE': (int, 'CodecSettings', -1),
    'CODEC_H264_PRESET': (str, 'CodecSettings', 'slow'),
    'CODEC_H264_PROFILE': (str, 'CodecSettings', 'high'),
    'CODEC_H264_QUALITY': (float, 'CodecSettings', 18.0),
    'CODEC_H264_TUNE': (str, 'CodecSettings', 'film'),
    'CODEC_H264_TWOPASS': (bool, 'CodecSettings', False),
    'CODEC_H264_TWOPASS_BITRATE': (int, 'CodecSettings', -1),
    'CODEC_HEVC_ADDITIONALOPT': (list, 'CodecSettings', [['pix_fmt', 'yuv420p10'],['x265-params', 'aq-mode=3']]),
    'CODEC_HEVC_AUTOMAXRATE': (bool, 'CodecSettings', True),
    'CODEC_HEVC_BUFSIZE': (int, 'CodecSettings', -1),
    'CODEC_HEVC_MAXRATE': (int, 'CodecSettings', -1),
    'CODEC_HEVC_PRESET': (str, 'CodecSettings', 'slow'),
    'CODEC_HEVC_QUALITY': (float, 'CodecSettings', 18.0),
    'CODEC_HEVC_TUNE': (str, 'CodecSettings', ''),
    'CODEC_HEVC_TWOPASS': (bool, 'CodecSettings', False),
    'CODEC_HEVC_TWOPASS_BITRATE': (int, 'CodecSettings', -1),
    'CODEC_VP8_QUALITY': (float, 'CodecSettings', 10),
    'CODEC_VP8_THREADS': (int, 'CodecSettings', 1),
    'DEFAULT_CODEC_AUDIO': (str, 'CodecSettings', 'copy'),
    'DEFAULT_CODEC_AUDIO_CONVERT': (bool, 'CodecSettings', False),
    'DEFAULT_CODEC_SUBTITLE': (str, 'CodecSettings', 'copy'),
    'DEFAULT_CODEC_SUBTITLE_CONVERT': (bool, 'CodecSettings', False),
    'DEFAULT_CODEC_VIDEO': (str, 'CodecSettings', 'HEVC'),
    'DEFAULT_CODEC_VIDEO_CONVERT': (bool, 'CodecSettings', True),
    'DO_NOT_OVERRIDE_GIT_BRANCH': (int, 'General', 0),
    'GIT_BRANCH': (str, 'General', 'master'),
    'GIT_PATH': (str, 'General', ''),
    'GIT_TOKEN': (str, 'General', ''),
    'GIT_USER': (str, 'General', 'Sonic-Y3k'),
    'LOG_BLACKLIST': (int, 'General', 1),
    'LOG_DIR': (str, 'General', ''),
    'OUTPUT_DIRECTORY': (str, 'General', ''),
    'SCAN_DIRECTORIES': (bool_int, 'General', 0),
    'SCAN_DIRECTORIES_INTERVAL': (int, 'General', 30),
    'SCAN_DIRECTORIES_PATH': (str, 'General', ''),
    'SEARCH_FILE_FORMATS': (list, 'General', [".3g2",".3gp",".asf",".avi",".divx",".flv",".m2ts",".m4v",".mj2",".mkv",".mov",".mp4",".mpeg",".mpg",".ogv",".rm",".rmvb",".vob",".wmv"]),
    'VERIFY_SSL_CERT': (bool_int, 'Advanced', 1),
}

_BLACKLIST_KEYS = []
_WHITELIST_KEYS = []

def make_backup(cleanup=False, scheduler=False):
    """ Makes a backup of config file, removes all but the last 5 backups """

    if scheduler:
        backup_file = 'config.backup-%s.sched.ini' % arrow.now().format('YYYYMMDDHHmmss')
    else:
        backup_file = 'config.backup-%s.ini' % arrow.now().format('YYYYMMDDHHmmss')
    backup_folder = pacvert.CONFIG.BACKUP_DIR
    backup_file_fp = os.path.join(backup_folder, backup_file)

    # In case the user has deleted it manually
    if not os.path.exists(backup_folder):
        os.makedirs(backup_folder)

    pacvert.CONFIG.write()
    shutil.copyfile(pacvert.CONFIG_FILE, backup_file_fp)

    if cleanup:
        # Delete all scheduled backup files except from the last 5.
        for root, dirs, files in os.walk(backup_folder):
            db_files = [os.path.join(root, f) for f in files if f.endswith('.sched.ini')]
            if len(db_files) > 5:
                backups_sorted_on_age = sorted(db_files, key=os.path.getctime, reverse=True)
                for file_ in backups_sorted_on_age[5:]:
                    try:
                        os.remove(file_)
                    except OSError as e:
                        logger.error(u"pacvert Config :: Failed to delete %s from the backup folder: %s" % (file_, e))

    if backup_file in os.listdir(backup_folder):
        logger.debug(u"pacvert Config :: Successfully backed up %s to %s" % (pacvert.CONFIG_FILE, backup_file))
        return True
    else:
        logger.warn(u"pacvert Config :: Failed to backup %s to %s" % (pacvert.CONFIG_FILE, backup_file))
        return False


# pylint:disable=R0902
# it might be nice to refactor for fewer instance variables
class Config(object):
    """ Wraps access to particular values in a config file """

    def __init__(self, config_file):
        """ Initialize the config with values from a file """
        self._config_file = config_file
        self._config = ConfigObj(self._config_file, encoding='utf-8')

        for key, value in sorted(_CONFIG_DEFINITIONS.iteritems(), key=lambda(v,k): (v,k)):
            self.check_setting(key)
        
        self._upgrade()
        self._blacklist()

    def _blacklist(self):
        """ Add tokens and passwords to blacklisted words in logger """
        blacklist = []

        for key, subkeys in self._config.iteritems():
            for subkey, value in subkeys.iteritems():
                if isinstance(value, basestring) and len(value.strip()) > 5 and \
                    subkey.upper() not in _WHITELIST_KEYS and any(bk in subkey.upper() for bk in _BLACKLIST_KEYS):
                    blacklist.append(value.strip())

        logger._BLACKLIST_WORDS = blacklist

    def _define(self, name):
        key = name.upper()
        ini_key = name.lower()
        definition = _CONFIG_DEFINITIONS[key]
        if len(definition) == 3:
            definition_type, section, default = definition
        else:
            definition_type, section, _, default = definition
        return key, definition_type, section, ini_key, default

    def check_section(self, section):
        """ Check if INI section exists, if not create it """
        if section not in self._config:
            self._config[section] = {}
            return True
        else:
            return False

    def check_setting(self, key):
        """ Cast any value in the config to the right type or use the default """
        key, definition_type, section, ini_key, default = self._define(key)
        self.check_section(section)
        try:
            my_val = definition_type(self._config[section][ini_key])
        except Exception:
            my_val = definition_type(default)
            self._config[section][ini_key] = my_val
        return my_val

    def write(self):
        """ Make a copy of the stored config and write it to the configured file """
        new_config = ConfigObj(encoding="UTF-8")
        new_config.filename = self._config_file

        # first copy over everything from the old config, even if it is not
        # correctly defined to keep from losing data
        for key, subkeys in self._config.items():
            if key not in new_config:
                new_config[key] = {}
            for subkey, value in subkeys.items():
                new_config[key][subkey] = value
        # next make sure that everything we expect to have defined is so
        for key in _CONFIG_DEFINITIONS.keys():
            key, definition_type, section, ini_key, default = self._define(key)
            self.check_setting(key)
            if section not in new_config:
                new_config[section] = {}
            new_config[section][ini_key] = self._config[section][ini_key]

        # Write it to file
        logger.info(u"pacvert Config :: Writing configuration to file")
        try:
            new_config.write()
        except IOError as e:
            logger.error(u"pacvert Config :: Error writing configuration file: %s", e)

        self._blacklist()

    def __getattr__(self, name):
        """
        Returns something from the ini unless it is a real property
        of the configuration object or is not all caps.
        """
        if not re.match(r'[A-Z_]+$', name):
            return super(Config, self).__getattr__(name)
        else:
            return self.check_setting(name)

    def __setattr__(self, name, value):
        """
        Maps all-caps properties to ini values unless they exist on the
        configuration object.
        """
        if not re.match(r'[A-Z_]+$', name):
            super(Config, self).__setattr__(name, value)
            return value
        else:
            key, definition_type, section, ini_key, default = self._define(name)
            self._config[section][ini_key] = definition_type(value)
            return self._config[section][ini_key]

    def process_kwargs(self, kwargs):
        """
        Given a big bunch of key value pairs, apply them to the ini.
        """
        for name, value in kwargs.items():
            key, definition_type, section, ini_key, default = self._define(name)
            self._config[section][ini_key] = definition_type(value)

    def _upgrade(self):
        """
        Upgrades config file from previous verisions and bumps up config version
        """
