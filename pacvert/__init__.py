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
import queue_worker
import scanner
import versioncheck
import pacvert.config
from helpers import sortQueue

PROG_DIR = None
FULL_PATH = None

ARGS = None
SIGNAL = None

SYS_PLATFORM = None
SYS_ENCODING = None

QUIET = False
VERBOSE = False
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

WORKING_QUEUE = []
IGNORE_QUEUE = []
FILEID = -1

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
        
        if not CONFIG.OUTPUT_DIRECTORY:
            CONFIG.OUTPUT_DIRECTORY = os.path.join(DATA_DIR, 'output')

        if not os.path.exists(CONFIG.OUTPUT_DIRECTORY):
            try:
                os.makedirs(CONFIG.OUTPUT_DIRECTORY)
            except OSError:
                if not QUIET:
                    sys.stderr.write("Unable to create the output directory.")

        # Start the logger, disable console if needed
        logger.initLogger(console=not QUIET, log_dir=CONFIG.LOG_DIR,
                          verbose=VERBOSE)

        if not CONFIG.BACKUP_DIR:
            CONFIG.BACKUP_DIR = os.path.join(DATA_DIR, 'backups')
        if not os.path.exists(CONFIG.BACKUP_DIR):
            try:
                os.makedirs(CONFIG.BACKUP_DIR)
            except OSError as e:
                logger.error("Could not create backup dir '%s': %s" % (CONFIG.BACKUP_DIR, e))

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
        try:
            CURRENT_VERSION, CONFIG.GIT_BRANCH = versioncheck.getVersion()
        except TypeError as e:
            logger.error("Something went terribly wrong by checking for the current version: "+str(e))
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
        if CONFIG.CHECK_GITHUB_ON_STARTUP and CONFIG.CHECK_GITHUB:
            try:
                LATEST_VERSION = versioncheck.checkGithub()
            except:
                logger.exception("Unhandled exception")
                LATEST_VERSION = CURRENT_VERSION
        else:
            LATEST_VERSION = CURRENT_VERSION

        # Store the original umask
        UMASK = os.umask(0)
        os.umask(UMASK)

        _INITIALIZED = True
        return True

def start():
    global started

    if _INITIALIZED:
        initialize_scheduler()
        started = True


def initialize_scheduler():
    """
    Start the scheduled background tasks. Re-schedule if interval settings changed.
    """

    with SCHED_LOCK:
        # Check if scheduler should be started
        start_jobs = not len(SCHED.get_jobs())

        # Update check
        if CONFIG.CHECK_GITHUB_INTERVAL and CONFIG.CHECK_GITHUB:
            minutes = CONFIG.CHECK_GITHUB_INTERVAL
        else:
            minutes = 0
        schedule_job(versioncheck.checkGithub, 'Check GitHub for updates', hours=0, minutes=minutes)

        # Scan for files
        if CONFIG.SCAN_DIRECTORIES and len(CONFIG.SCAN_DIRECTORIES_PATH) > 0:
            seconds = CONFIG.SCAN_DIRECTORIES_INTERVAL
        else:
            seconds = 0
        schedule_job(scanner.scan, 'Scan directories for new files', hours=0, minutes=0, seconds=seconds)

        #Update queue
        schedule_job(helpers.sortQueue, 'Resort queue', hours=0, minutes=0, seconds=10)
        
        # Work on queue
        #schedule_job(queue_worker.queue_worker, 'Work on queue', hours=0, minutes=0, seconds=5)

        # Start scheduler
        if start_jobs and len(SCHED.get_jobs()):
            try:
                SCHED.start()
            except Exception as e:
                logger.info(e)

def schedule_job(function, name, hours=0, minutes=0, seconds=0, args=None):
    """
    Start scheduled job if starting or restarting pacvert.
    Reschedule job if Interval Settings have changed.
    Remove job if if Interval Settings changed to 0
    """

    job = SCHED.get_job(name)
    if job:
        if hours == 0 and minutes == 0 and seconds == 0:
            SCHED.remove_job(name)
            logger.info("Removed background task: %s", name)
        elif job.trigger.interval != datetime.timedelta(hours=hours, minutes=minutes):
            SCHED.reschedule_job(name, trigger=IntervalTrigger(
                hours=hours, minutes=minutes, seconds=seconds), args=args)
            logger.info("Re-scheduled background task: %s", name)
    elif hours > 0 or minutes > 0 or seconds > 0:
        SCHED.add_job(function, id=name, trigger=IntervalTrigger(
            hours=hours, minutes=minutes, seconds=seconds), args=args)
        logger.info("Scheduled background task: %s", name)

def sig_handler(signum=None, frame=None):
    if signum is not None:
        logger.info("Signal %i caught, saving and exiting...", signum)
        shutdown()

def shutdown(restart=False, update=False):
    #cherrypy.engine.exit()
    SCHED.shutdown(wait=False)

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
