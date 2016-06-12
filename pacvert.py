#!/bin/sh
''''which python    >/dev/null 2>&1 && exec python    "$0" "$@" # '''
''''which python2   >/dev/null 2>&1 && exec python2   "$0" "$@" # '''
''''which python2.7 >/dev/null 2>&1 && exec python2.7 "$0" "$@" # '''
''''exec echo "Error: Python not found!" # '''

# -*- coding: utf-8 -*-

import os
import sys

# Ensure lib added to path, before any other imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib/'))

#general imports
import argparse
import locale
import signal
import time

import pacvert
from pacvert import config, logger

# Register signals, such as CTRL + C
signal.signal(signal.SIGINT, pacvert.sig_handler)
signal.signal(signal.SIGTERM, pacvert.sig_handler)

def main():
    """
    Pacvert application entry point. Parses arguments, setups encoding and
    initializes the application.
    """
    
    # Fixed paths to pacvert
    if hasattr(sys, 'frozen'):
        pacvert.FULL_PATH = os.path.abspath(sys.executable)
    else:
        pacvert.FULL_PATH = os.path.abspath(__file__)

    pacvert.PROG_DIR = os.path.dirname(pacvert.FULL_PATH)
    pacvert.ARGS = sys.argv[1:]

    # From sickbeard
    pacvert.SYS_PLATFORM = sys.platform
    pacvert.SYS_ENCODING = None

    try:
        locale.setlocale(locale.LC_ALL, "")
        pacvert.SYS_ENCODING = locale.getpreferredencoding()
    except (locale.Error, IOError):
        pass

    # for OSes that are poorly configured I'll just force UTF-8
    if not pacvert.SYS_ENCODING or pacvert.SYS_ENCODING in ('ANSI_X3.4-1968', 'US-ASCII', 'ASCII'):
        pacvert.SYS_ENCODING = 'UTF-8'
    
    # Set up and gather command line arguments
    parser = argparse.ArgumentParser(
        description='A Python based conversion tool.')

    parser.add_argument(
        '-v', '--verbose', action='store_true', help='Increase console logging verbosity')
    parser.add_argument(
        '-q', '--quiet', action='store_true', help='Turn off console logging')
    parser.add_argument(
        '-d', '--daemon', action='store_true', help='Run as a daemon')
    parser.add_argument(
        '-p', '--port', type=int, help='Force pacvert to run on a specified port')
    parser.add_argument(
        '--dev', action='store_true', help='Start pacvert in the development environment')
    parser.add_argument(
        '--datadir', help='Specify a directory where to store your data files')
    parser.add_argument(
        '--config', help='Specify a config file to use')
    parser.add_argument(
        '--nolaunch', action='store_true', help='Prevent browser from launching on startup')
    parser.add_argument(
        '--pidfile', help='Create a pid file (only relevant when running as a daemon)')

    args = parser.parse_args()

    if args.verbose:
        pacvert.VERBOSE = True
    if args.quiet:
        pacvert.QUIET = True
    
    
    # Do an intial setup of the logger.
    logger.initLogger(console=not pacvert.QUIET, log_dir=False,
                      verbose=pacvert.VERBOSE)
    
    if args.dev:
        pacvert.DEV = True
        logger.debug(u"pacvert is running in the dev environment.")

    if args.daemon:
        if sys.platform == 'win32':
            sys.stderr.write(
                "Daemonizing not supported under Windows, starting normally\n")
        else:
            pacvert.DAEMON = True
            pacvert.QUIET = True

    if args.pidfile:
        pacvert.PIDFILE = str(args.pidfile)

        # If the pidfile already exists, pacvert may still be running, so
        # exit
        if os.path.exists(pacvert.PIDFILE):
            raise SystemExit("PID file '%s' already exists. Exiting." %
                             pacvert.PIDFILE)

        # The pidfile is only useful in daemon mode, make sure we can write the
        # file properly
        if pacvert.DAEMON:
            pacvert.CREATEPID = True

            try:
                with open(pacvert.PIDFILE, 'w') as fp:
                    fp.write("pid\n")
            except IOError as e:
                raise SystemExit("Unable to write PID file: %s", e)
        else:
            logger.warn("Not running in daemon mode. PID file creation " \
                        "disabled.")

    # Determine which data directory and config file to use
    if args.datadir:
        pacvert.DATA_DIR = args.datadir
    else:
        pacvert.DATA_DIR = pacvert.PROG_DIR

    if args.config:
        config_file = args.config
    else:
        config_file = os.path.join(pacvert.DATA_DIR, config.FILENAME)

    # Try to create the DATA_DIR if it doesn't exist
    if not os.path.exists(pacvert.DATA_DIR):
        try:
            os.makedirs(pacvert.DATA_DIR)
        except OSError:
            raise SystemExit(
                'Could not create data directory: ' + pacvert.DATA_DIR + '. Exiting....')

    # Make sure the DATA_DIR is writeable
    if not os.access(pacvert.DATA_DIR, os.W_OK):
        raise SystemExit(
            'Cannot write to the data directory: ' + pacvert.DATA_DIR + '. Exiting...')

    # Put the database in the DATA_DIR
    #pacvert.DB_FILE = os.path.join(pacvert.DATA_DIR, database.FILENAME)

    if pacvert.DAEMON:
        pacvert.daemonize()

    # Read config and start logging
    pacvert.initialize(config_file)

    # Start the background threads
    pacvert.start()

    # Open connection for websocket
    #if pacvert.CONFIG.MONITORING_USE_WEBSOCKET:
    #    try:
    #        web_socket.start_thread()
    #    except:
    #        logger.warn(u"Websocket :: Unable to open connection.")
    #        # Fallback to polling
    #        pacvert.POLLING_FAILOVER = True
    #        pacvert.initialize_scheduler()

    # Force the http port if neccessary
    #if args.port:
    #    http_port = args.port
    #    logger.info('Using forced web server port: %i', http_port)
    #else:
    #    http_port = int(pacvert.CONFIG.HTTP_PORT)

    # Wait endlessy for a signal to happen
    while True:
        if not pacvert.SIGNAL:
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                pacvert.SIGNAL = 'shutdown'
        else:
            logger.info('Received signal: %s', pacvert.SIGNAL)

            if pacvert.SIGNAL == 'shutdown':
                pacvert.shutdown()
            elif pacvert.SIGNAL == 'restart':
                pacvert.shutdown(restart=True)
            else:
                pacvert.shutdown(restart=True, update=True)

            pacvert.SIGNAL = None

# Call main()
if __name__ == "__main__":
    main()
