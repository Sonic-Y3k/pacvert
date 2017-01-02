# This file is part of packvert.

import os

import pacvert
import logger

import cherrypy
from cherrypy.lib.static import serve_file, serve_download
from cherrypy._cperror import NotFound

from mako.lookup import TemplateLookup
from mako import exceptions

from helpers import sanitize, replace_illegal_chars

import json

def serve_template(templatename, **kwargs):
    interface_dir = os.path.join(str(pacvert.PROG_DIR), 'data/interfaces/')
    template_dir = os.path.join(str(interface_dir), pacvert.CONFIG.INTERFACE)

    _hplookup = TemplateLookup(directories=[template_dir], default_filters=['unicode', 'h'])

    server_name = "Pacvert"

    try:
        template = _hplookup.get_template(templatename)
        return template.render(http_root=pacvert.HTTP_ROOT, server_name=server_name,
                              **kwargs)
    except:
        return exceptions.html_error_template().render()

class WebInterface(object):
    """
    """

    def __init__(self):
        self.interface_dir = os.path.join(str(pacvert.PROG_DIR), 'data/')

    @cherrypy.expose
    def index(self, **kwargs):
        if pacvert.CONFIG.FIRST_RUN_COMPLETE:
            raise cherrypy.HTTPRedirect(pacvert.HTTP_ROOT + "home")
        else:
            raise cherrypy.HTTPRedirect(pacvert.HTTP_ROOT + "welcome")

    ##### Welcome #####
    @cherrypy.expose
    def welcome(self, **kwargs):
        config = {
        }

        # The setup wizard just refreshes the page on submit so we must redirect to home if config set.
        if pacvert.CONFIG.FIRST_RUN_COMPLETE:
            pacvert.initialize_scheduler()
            raise cherrypy.HTTPRedirect(pacvert.HTTP_ROOT + "home")
        else:
            return serve_template(templatename="welcome.html", title="Welcome", config=config)

    ##### home #####
    @cherrypy.expose
    def home(self, **kwargs):
        queueLength = len(pacvert.WORKING_QUEUE)
        return serve_template(templatename="home.html", title="Home", queueLength=queueLength)
        
    ##### update home #####
    @cherrypy.expose
    def update(self, start=None, end=None, updateName=None, updateID=None, up=None, down=None, remove=None):
        try:
            start = int(start)
            end = int(end)
        except TypeError:
            start = 0
            end = 20
        
        if not up is None:
            up = int(up)
            if up > 1 and up < len(pacvert.WORKING_QUEUE):
                pacvert.WORKING_QUEUE[up], pacvert.WORKING_QUEUE[up-1] = pacvert.WORKING_QUEUE[up-1], pacvert.WORKING_QUEUE[up]
                return "OK."
        
        if not down is None:
            down = int(down)
            if down > 0 and down < len(pacvert.WORKING_QUEUE):
                pacvert.WORKING_QUEUE[down], pacvert.WORKING_QUEUE[down+1] = pacvert.WORKING_QUEUE[down+1], pacvert.WORKING_QUEUE[down]
                return "OK."
        
        if not remove is None:
            remove = int(remove)
            if remove > 0 and remove < len(pacvert.WORKING_QUEUE):
                pacvert.IGNORE_QUEUE.append(pacvert.WORKING_QUEUE[remove].fullpath)
                del pacvert.WORKING_QUEUE[remove]
                return "OK."
        
        if not updateName is None:
            try:
                updateName = replace_illegal_chars(sanitize(str(updateName)))
                if (len(updateName) < 2):
                    return "Illegal character detected."
                updateID = int(updateID)
                pacvert.WORKING_QUEUE[start+updateID].setRename(updateName)
                return "OK."
            except ValueError:
                logger.error("Can't update name of file.")         
        
        retValue = []
        if len(pacvert.WORKING_QUEUE) > 0:
            for i in range(min(start, len(pacvert.WORKING_QUEUE)), min(len(pacvert.WORKING_QUEUE),end)):
                retValue.append(pacvert.WORKING_QUEUE[i].getAsDict())
            
        return json.dumps(retValue)
