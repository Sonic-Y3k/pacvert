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
        return serve_template(templatename="home.html", title="Home")

    ##### home #####
    @cherrypy.expose
    def home(self, **kwargs):
        return serve_template(templatename="home.html", title="Home")

    ##### update home #####
    @cherrypy.expose
    def update(self, start=None, end=None, status_filter=None, updateName=None, updateID=None, up=None, down=None, remove=None, pause=None):
        try:
            start = int(start)
            end = int(end)
            status_filter = int(status_filter)
        except TypeError:
            start = 0
            end = 20
            status_filter = -1
        
        if pause is not None:
            try:
                pause = int(pause)
            except TypeError:
                pause = 0
            
            if pause == 1:
                pacvert.PAUSE = True
            else:
                pacvert.PAUSE = False
        
        if not up is None:
            try:
                with pacvert.QUEUE_LOCK:
                    pacvert.QUEUE.move(int(up), -1)
                return "OK."
            except:
                return "Nope."
        
        if not down is None:
            try:
                with pacvert.QUEUE_LOCK:
                    pacvert.QUEUE.move(int(down), 1)
                return "OK."
            except:
                return "Nope."
        
        if not remove is None:
            try:
                with pacvert.QUEUE_LOCK:
                    pacvert.QUEUE.remove(int(remove))
                return "OK."
            except:
                return "Nope."

        if updateName is not None and updateID is not None:
            try:
                updateName = replace_illegal_chars(sanitize(str(updateName)))
                if (len(updateName) < 2):
                    return "Illegal character detected."
                updateID = int(updateID)
                returnQueueElementByFileID(updateID).output_rename(updateName)
                return "OK."
            except Exception as e:
                logger.error("Can't update name of file."+e.message)

        retValue = []
        with pacvert.QUEUE_LOCK:
            tempQueue = pacvert.QUEUE.get_all(status_filter)
        
        retValue.append({'queue_length': len(tempQueue), 'commits_behind': pacvert.COMMITS_BEHIND, 'pause': int(pacvert.PAUSE), 'page_size': int(pacvert.CONFIG.DEFAULT_PAGE_SIZE)})
        if len(tempQueue) > 0:
            for i in range(min(start, len(tempQueue)), min(len(tempQueue),end)):
                retValue.append(tempQueue[i].export_object())
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
