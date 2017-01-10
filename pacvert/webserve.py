# This file is part of packvert.

import os

import pacvert
import logger

import cherrypy
from cherrypy.lib.static import serve_file, serve_download
from cherrypy._cperror import NotFound

from mako.lookup import TemplateLookup
from mako import exceptions

from helpers import sanitize, replace_illegal_chars, returnQueueElementByFileID, cast_to_float, cast_to_int
from config import _CONFIG_DEFINITIONS

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
            raise cherrypy.HTTPRedirect(pacvert.HTTP_ROOT + "home")
            

    ##### Welcome #####
    @cherrypy.expose
    def welcome(self, **kwargs):
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
    def update(self, start=None, end=None, statusFilter=None, updateName=None, updateID=None, up=None, down=None, remove=None):
        try:
            start = int(start)
            end = int(end)
            statusFilter = int(statusFilter)
        except TypeError:
            start = 0
            end = 20
            statusFilter = -1
        
        if not up is None:
            up = pacvert.WORKING_QUEUE.index(returnQueueElementByFileID(int(up)))
            if up > 1 and up < len(pacvert.WORKING_QUEUE):
                pacvert.WORKING_QUEUE[up], pacvert.WORKING_QUEUE[up-1] = pacvert.WORKING_QUEUE[up-1], pacvert.WORKING_QUEUE[up]
                return "OK."
        
        if not down is None:
            down = pacvert.WORKING_QUEUE.index(returnQueueElementByFileID(int(down)))
            if down > 0 and down < len(pacvert.WORKING_QUEUE):
                pacvert.WORKING_QUEUE[down], pacvert.WORKING_QUEUE[down+1] = pacvert.WORKING_QUEUE[down+1], pacvert.WORKING_QUEUE[down]
                return "OK."
        
        if not remove is None:
            remove = pacvert.WORKING_QUEUE.index(returnQueueElementByFileID(int(remove)))
            if remove >= 0 and remove < len(pacvert.WORKING_QUEUE):
                pacvert.IGNORE_QUEUE.append(pacvert.WORKING_QUEUE[remove].fullpath)
                del pacvert.WORKING_QUEUE[remove]
                return "OK."
        
        if not updateName is None:
            try:
                updateName = replace_illegal_chars(sanitize(str(updateName)))
                if (len(updateName) < 2):
                    return "Illegal character detected."
                updateID = int(updateID)
                returnQueueElementByFileID(updateID).setRename(updateName)
                return "OK."
            except ValueError:
                logger.error("Can't update name of file.")         
        
        retValue = []
        tempQueue = []
        for i in pacvert.WORKING_QUEUE:
            if statusFilter >= 0:
                if i.status == statusFilter:
                    tempQueue.append(i)
            else:
                tempQueue.append(i)
        if len(tempQueue) > 0:
            for i in range(min(start, len(tempQueue)), min(len(tempQueue),end)):
                retValue.append(tempQueue[i].getAsDict())
        
        retValue.append({'queue_length': len(tempQueue)})
        return json.dumps(retValue)
        
    @cherrypy.expose
    def settings(self, getConfigVal=None, paramName=None, paramVal=None):
        if (not paramName is None) and (not paramVal is None):
            try:
                if not str(pacvert.CONFIG.__getattr__(paramName)) is paramVal:
                    if type(_CONFIG_DEFINITIONS[paramName][2]) is dict:
                        result = {}
                        if len(paramVal) > 0:
                            firstSplit = str(paramVal).split(",")
                            for elem in firstSplit:
                                secondSplit = elem.split(":")
                                result[secondSplit[0]] = str(secondSplit[1])                            
                            pacvert.CONFIG.__setattr__(paramName, result)
                    elif type(_CONFIG_DEFINITIONS[paramName][2]) is list:
                        pacvert.CONFIG.__setattr__(paramName, paramVal.split(","))
                    elif type(_CONFIG_DEFINITIONS[paramName][2]) is float:
                        pacvert.CONFIG.__setattr__(paramName, cast_to_float(paramVal))
                    elif type(_CONFIG_DEFINITIONS[paramName][2]) is int:
                        pacvert.CONFIG.__setattr__(paramName, cast_to_int(paramVal))
                    else:
                        pacvert.CONFIG.__setattr__(paramName, paramVal)
                pacvert.CONFIG.FIRST_RUN_COMPLETE = True
                return "OK."
            except:
                 return "Nope."
        if not getConfigVal is None:
            tempConfig = {'General': {}, 'CodecSettings': {}, 'Advanced': {}}
            for element in _CONFIG_DEFINITIONS:
                if type(_CONFIG_DEFINITIONS[element][2]) is str:
                    thistype = "str"
                elif type(_CONFIG_DEFINITIONS[element][2]) is int:
                    thistype = "int"
                elif type(_CONFIG_DEFINITIONS[element][2]) is float:
                    thistype = "float"
                elif type(_CONFIG_DEFINITIONS[element][2]) is dict:
                    thistype = "dict"
                elif type(_CONFIG_DEFINITIONS[element][2]) is bool:
                    thistype = "bool"
                elif type(_CONFIG_DEFINITIONS[element][2]) is list:
                    thistype = "list"
                else:
                    thistype = "unknown"
                tempConfig[_CONFIG_DEFINITIONS[element][1]][element] = {'value': pacvert.CONFIG.__getattr__(element), 'type': thistype}
                    

            return json.dumps(tempConfig)
        return "Nope."#serve_template(templatename="settings.html", title="Settings")
