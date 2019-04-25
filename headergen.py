import time
import sys
import os
import re
import pickle
import shutil
import tempfile
import depfinder
import curprj
import util
import logging
import classfileheadergen
import enumfileheadergen
import traceback
from classmember import ClassMember

file_data_cache = {}

def generateHeaderForCppFile(fn):
    cur_mtime = os.path.getmtime(fn)
    old_mtime = file_data_cache[fn]['mtime'] if fn in file_data_cache else 0

    if cur_mtime > old_mtime:
        members = []
        logging.debug(fn)

        tfn = fn.replace('Private', 'Public').replace('.cpp', '.h')
        if not os.path.isdir(os.path.dirname(tfn)): os.makedirs(os.path.dirname(tfn))

        className = re.search('([A-Z0-9a-z]+)\\.cpp', fn).group(1)

        extends = []
        isClassFile = False
        classMods = ''
        isInFunction = False
        currentFunction = None
        is_enum_file = False
        enum_values = []

        try:
            with open(fn) as f:
                for l in f:
                    m = re.match('extends\\s*\\(([^)]+)\\)', l)
                    if m:
                        if m.group(1)[0] in ['U', 'E', 'F', 'T', 'A']:
                            className = m.group(1)[0] + className
                        extends = m.group(1).split(' ')
                        isClassFile = True

                    if isClassFile:
                        if (re.match("\\S.+", l)):
                            newMember = ClassMember.createFromLine(l)

                            if newMember:
                                members.append(newMember)

                                if newMember.type == 'FUNCTION': currentFunction = newMember

                        if l.startswith('}'):
                            logging.debug("End of function")
                            currentFunction = None

                        if 'Super::' in l and currentFunction:
                            logging.debug("Found Super::")
                            currentFunction.isOverride = True

                        #
                        m = re.match('blueprintEvent\\((?P<event>[^()]+)(\\((?P<args>[^)]+)\\))?\\)', l)
                        if m:
                            members.append(ClassMember('FUNCTION', cppType='void', name=m.group('event'), access='public', isConst=False, mods='BlueprintImplementableEvent', args=m.group('args')))

                        m = re.match('classMods\\((?P<mods>.+)\\)', l)
                        if m:
                            classMods = util.join_list(util.split_list(m.group('mods')))

                    m = re.match('enumValue\\((?P<value>[^)]+)\\)', l)
                    if m:
                        is_enum_file = True
                        enum_values.append(m.group('value'))
        except Exception as ex:
            logging.error("Error parsing CPP: " + str(ex) + '\n' + traceback.format_exc())

        file_data_cache[fn] = {
            'members': members,
            'className': className,
            'extends': extends,
            'classMods': classMods,
            'enum_values': enum_values,
            'mtime': cur_mtime,
            'isClassFile': isClassFile,
            'is_enum_file': is_enum_file,
            'tfn': tfn,
        }

    d = file_data_cache[fn]


    if d['isClassFile']: return classfileheadergen.generate_class_file_header(fn, list(d['members']), d['tfn'], d['className'], d['extends'], d['classMods'])
    if d['is_enum_file']: return enumfileheadergen.generate_enum_file_header(fn, list(d['enum_values']), d['tfn'], d['className'], d['classMods'])

    logging.debug("Cannot generate header for " + fn)

    return None
