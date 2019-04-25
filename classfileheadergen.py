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

    replicated_properties = []

    for mem in members:
        if mem.generateGetter:
            getterName = 'Get' + mem.name
            if getterName not in memberNames:
                members.append(ClassMember('FUNCTION', cppType=mem.cppType, name=getterName, access='public', isConst=False, mods='BlueprintGetter'))
                getterSetterImpls += '{retTyp} {className}::{getterName}(){{ return {name}; }}\n'.format(retTyp=mem.cppType, className=className, getterName=getterName, name=mem.name)
        if mem.generateSetter:
            setterName = 'Set' + mem.name
            if setterName not in memberNames:
                members.append(ClassMember('FUNCTION', cppType='void', name=setterName, access='public', isConst=False, args='{retTyp} value'.format(retTyp=mem.cppType), mods='BlueprintSetter'))
                getterSetterImpls += 'void {className}::{setterName}({retTyp} value){{ {name} = value; }}\n'.format(retTyp=mem.cppType, className=className, setterName=setterName, name=mem.name)

        # The "Server" mod means this is a function that is called on the server
        if 'Server' in mem.get_mod_list():
            # Figure out what the validator name for this server function is
            validator_name = mem.name.replace('_Implementation', '_Validate')
            if validator_name not in memberNames:
                # The validator MUST exist, so if it's not already a member create a fake one
                getterSetterImpls += f'bool {className}::{validator_name}({mem.args}){{ return true; }}\n'

        if 'Replicated' in mem.get_mod_list():
            replicated_properties.append(mem.name)

    if replicated_properties:
        getterSetterImpls += '#include "UnrealNetwork.h"\n'
        getterSetterImpls += 'void fun::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const\n{\n\tSuper::GetLifetimeReplicatedProps(OutLifetimeProps);\n'

        for replicated_property in replicated_properties:
            getterSetterImpls += f'\tDOREPLIFETIME({className}, {replicated_property});\n'

        getterSetterImpls += '}\n'

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
            logging.debug("During processing of {className}, can't find header for class {name}: {ex}".format(className=className, name=ext, ex=ex))

    for header in depfinder.findDependentHeaders(fn, 'E[A-Za-z0-9]+'):
        ret += '#include "{header}"\n'.format(header=header)

    ret += '#include "' + className[1:] + '.generated.h"\n'

    ret += '\n'
    ret += 'U' + classType.upper() + '(' + classMods + ')\n'
    ret += classType + ' ' + curprj.prjName.upper() + '_API ' + className

    # "FStruct" is magical. It tells the system that this is a struct, but not to actually add in the extends syntax, as FStruct does not actually exist
    if 'FStruct' not in extends: ret += ' : public ' + ', '.join(extends)
    ret += '\n'
    ret += '{\n'
    ret += '\tGENERATED_BODY()\n'
    lastProtLevel = ''

    members.sort(key=lambda x: x.access)

    for m in members:
        # If the class is bare then implicitly all members are too
        if ('bare' in classMods or (classType == 'struct' and m.type == 'FUNCTION')):
            m.bare = True

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
#ifdef fun
    #undef fun
#endif

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