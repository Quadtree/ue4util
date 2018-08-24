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
from classmember import ClassMember

def generate_class_file_header(fn, members, tfn, className, extends, classMods):
    memberNames = [x.name for x in members]
    logging.debug(memberNames)

    getterSetterImpls = ''

    for mem in members:
        if mem.generateGetter:
            getterName = 'Get' + mem.name
            members.append(ClassMember('FUNCTION', cppType=mem.cppType, name=getterName, access='public', isConst=False, mods='BlueprintPure'))
            if getterName not in memberNames:
                getterSetterImpls += '{retTyp} {className}::{getterName}(){{ return {name}; }}\n'.format(retTyp=mem.cppType, className=className, getterName=getterName, name=mem.name)
        if mem.generateSetter:
            setterName = 'Set' + mem.name
            members.append(ClassMember('FUNCTION', cppType='void', name=setterName, access='public', isConst=False, args='{retTyp} value'.format(retTyp=mem.cppType)))
            if setterName not in memberNames:
                getterSetterImpls += 'void {className}::{setterName}({retTyp} value){{ {name} = value; }}\n'.format(retTyp=mem.cppType, className=className, setterName=setterName, name=mem.name)

    logging.debug('extends ' + ', '.join(extends))

    defDependentClasses = list(extends)
    for mem in members:
        if mem.cppType and mem.cppType[0] == mem.cppType[0].upper() and not '*' in mem.cppType: defDependentClasses.append(mem.cppType)

    logging.debug('defDependentClasses={defDependentClasses}'.format(defDependentClasses=defDependentClasses))

    if className[0] == 'F':
        classType = 'struct'
    elif className[0] == 'E':
        classType = 'enum'
    else:
        classType = 'class'

    ret = '#pragma once\n\n'
    ret += '#include "EngineMinimal.h"\n'
    for ext in defDependentClasses:
        try:
            ret += '#include "' + depfinder.findClassHeader(ext) + '"\n'
        except Exception as ex:
            logging.info("During processing of {className}, can't find header for class {name}: {ex}".format(className=className, name=ext, ex=ex))

    for header in depfinder.findDependentHeaders(fn, 'E[A-Za-z0-9]+'):
        ret += '#include "{header}"\n'.format(header=header)

    ret += '#include "' + className[1:] + '.generated.h"\n'

    ret += '\n'
    ret += 'U' + classType.upper() + '(' + classMods + ')\n'
    ret += classType + ' ' + curprj.prjName.upper() + '_API ' + className + ' : public ' + ', '.join(extends) + '\n'
    ret += '{\n'
    ret += '\tGENERATED_BODY()\n'
    lastProtLevel = ''

    members.sort(key=lambda x: x.access)

    for m in members:
        if m.access != lastProtLevel:
            ret += (m.access + ':\n')
            lastProtLevel = m.access
        ret += m.render() + '\n'

    ret += '};\n'
    logging.debug(ret)


    logging.debug(tfn)
    util.replaceIfModified(tfn, ret)

    tfn = fn.replace('Private', 'Public').replace('.cpp', '.ac.h')

    pbt = """
#define mods(...)
#define im(...)
#define blueprintEvent(...)
#define prop(...)
#define extends(...)
#define classMods(...)
#define fun         {className}
{getterSetterImpls}
""".format(className=className, getterSetterImpls=getterSetterImpls, extends=extends[0])

    for header in depfinder.findDependentHeaders(fn):
        pbt += '#include "{header}"\n'.format(header=header)

    util.replaceIfModified(tfn, pbt)



    return True