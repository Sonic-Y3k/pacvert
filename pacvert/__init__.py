# This file is part of Pacvert.

import os
import sqlite3
import sys
import subprocess
import threading
import datetime
#import uuid
# Some cut down versions of Python may not include this module and it's not critical for us
#try:
#    import webbrowser
#    no_browser = False
#except ImportError:
#    no_browser = True

#import cherrypy
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

import config
#import database
import logger
#import versioncheck
import pacvert.config

PROG_DIR = None
FULL_PATH = None

ARGS = None
SIGNAL = None

SYS_PLATFORM = None
SYS_ENCODING = None

QUIET = False
VERBOSE = True
DAEMON = False
CREATEPID = False
PIDFILE = None

SCHED = BackgroundScheduler()
SCHED_LOCK = threading.Lock()

INIT_LOCK = threading.Lock()
_INITIALIZED = False
started = False

DATA_DIR = None

CONFIG = None
CONFIG_FILE = None

DB_FILE = None

INSTALL_TYPE = None
CURRENT_VERSION = None
LATEST_VERSION = None
COMMITS_BEHIND = None

UMASK = None

POLLING_FAILOVER = False

HTTP_ROOT = None

DEV = False


def initialize(config_file):
    with INIT_LOCK:

        global CONFIG
        global CONFIG_FILE
        global _INITIALIZED
        global CURRENT_VERSION
        global LATEST_VERSION
        global UMASK
        global POLLING_FAILOVER
        CONFIG = pacvert.config.Config(config_file)
        CONFIG_FILE = config_file

        assert CONFIG is not None

        if _INITIALIZED:
            return False

        #if CONFIG.HTTP_PORT < 21 or CONFIG.HTTP_PORT > 65535:
        #    pacvert.logger.warn(
        #        'HTTP_PORT out of bounds: 21 < %s < 65535', CONFIG.HTTP_PORT)
        #    CONFIG.HTTP_PORT = 8181

        #if not CONFIG.HTTPS_CERT:
        #    CONFIG.HTTPS_CERT = os.path.join(DATA_DIR, 'server.crt')
        #if not CONFIG.HTTPS_KEY:
        #    CONFIG.HTTPS_KEY = os.path.join(DATA_DIR, 'server.key')

        if not CONFIG.LOG_DIR:
            CONFIG.LOG_DIR = os.path.join(DATA_DIR, 'logs')

        if not os.path.exists(CONFIG.LOG_DIR):
            try:
                os.makedirs(CONFIG.LOG_DIR)
            except OSError:
                CONFIG.LOG_DIR = None

                if not QUIET:
                    sys.stderr.write("Unable to create the log directory. " \
                                     "Logging to screen only.\n")

        # Start the logger, disable console if needed
        logger.initLogger(console=not QUIET, log_dir=CONFIG.LOG_DIR,
                          verbose=VERBOSE)

        #if not CONFIG.BACKUP_DIR:
        #    CONFIG.BACKUP_DIR = os.path.join(DATA_DIR, 'backups')
        #if not os.path.exists(CONFIG.BACKUP_DIR):
        #    try:
        #        os.makedirs(CONFIG.BACKUP_DIR)
        #    except OSError as e:
        #        logger.error("Could not create backup dir '%s': %s" % (CONFIG.BACKUP_DIR, e))

        #if not CONFIG.CACHE_DIR:
        #    CONFIG.CACHE_DIR = os.path.join(DATA_DIR, 'cache')
        #if not os.path.exists(CONFIG.CACHE_DIR):
        #    try:
        #        os.makedirs(CONFIG.CACHE_DIR)
        #    except OSError as e:
        #        logger.error("Could not create cache dir '%s': %s" % (CONFIG.CACHE_DIR, e))

        # Initialize the database
        #logger.info('Checking to see if the database has all tables....')
        #try:
        #    dbcheck()
        #except Exception as e:
        #    logger.error("Can't connect to the database: %s" % e)

        # Check if pacvert has a uuid
        #if CONFIG.PMS_UUID == '' or not CONFIG.PMS_UUID:
        #    my_uuid = generate_uuid()
        #    CONFIG.__setattr__('PMS_UUID', my_uuid)
        #    CONFIG.write()

        # Get the currently installed version. Returns None, 'win32' or the git
        # hash.
        #CURRENT_VERSION, CONFIG.GIT_BRANCH = versioncheck.getVersion()

        # Write current version to a file, so we know which version did work.
        # This allowes one to restore to that version. The idea is that if we
        # arrive here, most parts of pacvert seem to work.
        if CURRENT_VERSION:
            version_lock_file = os.path.join(DATA_DIR, "version.lock")

            try:
                with open(version_lock_file, "w") as fp:
                    fp.write(CURRENT_VERSION)
            except IOError as e:
                logger.error("Unable to write current version to file '%s': %s" %
                             (version_lock_file, e))

        # Check for new versions
        #if CONFIG.CHECK_GITHUB_ON_STARTUP and CONFIG.CHECK_GITHUB:
        #    try:
        #        LATEST_VERSION = versioncheck.checkGithub()
        #    except:
        #        logger.exception("Unhandled exception")
        #        LATEST_VERSION = CURRENT_VERSION
        #else:
        #    LATEST_VERSION = CURRENT_VERSION

        # Store the original umask
        UMASK = os.umask(0)
        os.umask(UMASK)

        _INITIALIZED = True
        return True

def start():
    global started

    if _INITIALIZED:
        started = True


def sig_handler(signum=None, frame=None):
    if signum is not None:
        logger.info("Signal %i caught, saving and exiting...", signum)
        shutdown()

def shutdown(restart=False, update=False):
    #cherrypy.engine.exit()
    #SCHED.shutdown(wait=False)

    CONFIG.write()

    if not restart and not update:
        logger.info('pacvert is shutting down...')

    if update:
        logger.info('pacvert is updating...')
        try:
            versioncheck.update()
        except Exception as e:
            logger.warn('pacvert failed to update: %s. Restarting.' % e)

    if CREATEPID:
        logger.info('Removing pidfile %s', PIDFILE)
        os.remove(PIDFILE)

    if restart:
        logger.info('pacvert is restarting...')
        exe = sys.executable
        args = [exe, FULL_PATH]
        args += ARGS
        if '--nolaunch' not in args:
            args += ['--nolaunch']
        logger.info('Restarting pacvert with %s', args)

        # os.execv fails with spaced names on Windows
        # https://bugs.python.org/issue19066
        if os.name == 'nt':
            subprocess.Popen(args, cwd=os.getcwd())
        else:
            os.execv(exe, args)

    os._exit(0)


def generate_uuid():
    logger.debug(u"Generating UUID...")
    return uuid.uuid4().hex