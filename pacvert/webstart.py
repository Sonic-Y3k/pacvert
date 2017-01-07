# This file is part of pacvert.

import os

import pacvert
import cherrypy
import logger

from pacvert.helpers import create_https_certificates
from pacvert.webserve import WebInterface

def initialize(options):
    """
    """

    # HTTPS stuff stolen from sickbeard
    enable_https = options['enable_https']
    https_cert = options['https_cert']
    https_key = options['https_key']

    enable_https = False
    if enable_https:
        # If either the HTTPS certificate or key do not exist, try to make self-signed ones.
        if pacvert.CONFIG.HTTPS_CREATE_CERT and \
            (not (https_cert and os.path.exists(https_cert)) or not (https_key and os.path.exists(https_key))):
            if not create_https_certificates(https_cert, https_key):
                logger.warn(u"Pacvert WebStart :: Unable to create certificate and key. Disabling HTTPS")
                enable_https = False

        if not (os.path.exists(https_cert) and os.path.exists(https_key)):
            logger.warn(u"Pacvert WebStart :: Disabled HTTPS because of missing certificate and key.")
            enable_https = False

    options_dict = {
        'server.socket_port': options['http_port'],
        'server.socket_host': options['http_host'],
        'environment': options['http_environment'],
        'server.thread_pool': 10,
        'tools.encode.on': True,
        'tools.encode.encoding': 'utf-8',
        'tools.decode.on': True
    }

    if enable_https:
        options_dict['server.ssl_certificate'] = https_cert
        options_dict['server.ssl_private_key'] = https_key
        protocol = "https"
    else:
        protocol = "http"

    if options['http_password']:
        logger.info(u"Pacvert WebStart :: Web server authentication is enabled, username is '%s'", options['http_username'])
        if options['http_basic_auth']:
            auth_enabled = session_enabled = False
            basic_auth_enabled = True
        else:
            options_dict['tools.sessions.on'] = auth_enabled = session_enabled = True
            basic_auth_enabled = False
            cherrypy.tools.auth = cherrypy.Tool('before_handler', webauth.check_auth)
    else:
        auth_enabled = session_enabled = basic_auth_enabled = False

    if not options['http_root'] or options['http_root'] == '/':
        pacvert.HTTP_ROOT = options['http_root'] = '/'
    else:
        pacvert.HTTP_ROOT = options['http_root'] = '/' + options['http_root'].strip('/') + '/'

    cherrypy.config.update(options_dict)

    #some parts missing
    conf = {
        '/': {
            'tools.staticdir.root': os.path.join(pacvert.PROG_DIR, 'data'),
            'tools.proxy.on': options['http_proxy'],  # pay attention to X-Forwarded-Proto header
            'tools.gzip.on': True,
            'tools.gzip.mime_types': ['text/html', 'text/plain', 'text/css',
                                      'text/javascript', 'application/json',
                                      'application/javascript'],
            'tools.auth.on': auth_enabled,
            'tools.sessions.on': session_enabled,
            'tools.sessions.timeout': 30 * 24 * 60,  # 30 days
            'tools.auth_basic.on': basic_auth_enabled,
            'tools.auth_basic.realm': 'Pacvert web server',
            'tools.auth_basic.checkpassword': cherrypy.lib.auth_basic.checkpassword_dict({
                options['http_username']: options['http_password']})
        },
        '/css': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': "interfaces/default/css",
            'tools.caching.on': False,
            'tools.caching.force': False,
            'tools.caching.delay': 0,
            'tools.expires.on': True,
            'tools.expires.secs': 1,  # 1 second
            'tools.auth.on': False,
            'tools.sessions.on': False
        },
        '/fonts': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': "interfaces/default/fonts",
            'tools.caching.on': True,
            'tools.caching.force': True,
            'tools.caching.delay': 0,
            'tools.expires.on': True,
            'tools.expires.secs': 60 * 60 * 24 * 30,  # 30 days
            'tools.auth.on': False,
            'tools.sessions.on': False
        },
        '/js': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': "interfaces/default/js",
            'tools.caching.on': False,
            'tools.caching.force': False,
            'tools.caching.delay': 0,
            'tools.expires.on': True,
            'tools.expires.secs': 1,  # 1 second
            'tools.auth.on': False,
            'tools.sessions.on': False
        },
        '/images': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': "interfaces/default/images",
            'tools.caching.on': False,
            'tools.caching.force': False,
            'tools.caching.delay': 0,
            'tools.expires.on': True,
            'tools.expires.secs': 60 * 60 * 24 * 30,  # 30 days
            'tools.auth.on': False,
            'tools.sessions.on': False
        },
    }

    # Prevent time-outs
    cherrypy.engine.timeout_monitor.unsubscribe()
    cherrypy.tree.mount(WebInterface(), options['http_root'], config=conf)

    try:
        logger.info(u"Pacvert WebStart :: Starting Pacvert web server on %s://%s:%d%s", protocol,
                    options['http_host'], options['http_port'], options['http_root'])
        cherrypy.process.servers.check_port(str(options['http_host']), options['http_port'])

        cherrypy.server.start()
    except IOError:
        sys.stderr.write('Failed to start on port: %i. Is something else running?\n' % (options['http_port']))
        sys.exit(1)

    cherrypy.server.wait()
