import time
import sys
import os
import re
import pickle
import shutil
import tempfile
import depfinder

class ClassMember:
    def __init__(self, typ, cppType, name, access, isConst, className = None, mods = None, args = None, bare=False):
        self.type = str(typ)
        self.cppType = cppType
        self.name = name
        self.isConst = isConst
        self.bare = bare
        self.isStatic = False
        self.access = access

        if not mods: mods = ''

        modList = []
        if mods: modList = [x.strip() for x in mods.split(' ')]

        print('modList=' + str(modList))

        for accessLevel in ['privateGS', 'protectedGS', 'publicGS', 'private', 'protected', 'public']:
            if accessLevel in modList:
                self.access = accessLevel
                modList.remove(accessLevel)
                break

        print('access=' + self.access + ',type=' + self.type)

        if 'bare' in modList:
            modList.remove('bare')
            self.bare = True

        if 'static' in modList:
            modList.remove('static')
            self.isStatic = True

        self.generateGetter = 'G' in self.access
        self.generateSetter = 'S' in self.access
        self.access = self.access.replace('G', '').replace('S', '')

        if self.type == 'PROPERTY':
            modList.append('SaveGame')

            if self.access == 'public':
                modList.append('BlueprintReadWrite')

                if ('Component' in cppType):
                    modList.append('VisibleAnywhere')
                else:
                    modList.append('EditAnywhere')
            else:
                print("NOT PUBLIC '{access}' != 'public'".format(access=self.access))

        print('modList=' + str(modList))

        if self.type == 'FUNCTION':
            if not 'BlueprintPure' in mods and not 'BlueprintImplementableEvent' in mods:
                modList.append('BlueprintCallable')

            if (self.access == 'private' and 'BlueprintCallable' in modList):
                modList.remove('BlueprintCallable')

        self.mods = ', '.join(modList)
        self.args = args
        self.className = className

    def createFromLine(line):
        m = re.match("prop\\(((?P<mods>[^)]+?)\\s+)?(?P<typ>[A-Za-z0-9]+(<[^>]+>)?\\s*\\*?)\\s+(?P<name>[A-Za-z0-9*]+)\\)", line)
        if (m):
            return ClassMember(
                typ='PROPERTY',
                cppType=m.group('typ'),
                name=m.group('name'),
                access='privateGS',
                isConst=False,
                className='Class',
                mods=m.group('mods'),
                args=None,
                bare=False)

        m = re.search("(mods\\((?P<mods>[^)]+)\\)\\s+)?((?P<retTyp>[A-Za-z0-9 *<>,]+)?\\s+)?fun::(?P<funcName>[A-Za-z0-9]+)\\s*\\((?P<args>[^)]*)\\)", line)
        if (m):
            print('cppType=' + str(m.group('retTyp')))
            return ClassMember(
                typ='FUNCTION',
                cppType=m.group('retTyp'),
                name=m.group('funcName'),
                access='public',
                isConst=False,
                className='Class',
                mods=m.group('mods'),
                args=m.group('args'),
                bare=False)

    def transformArgToHeader(arg):
        if 'class' in arg or 'struct' in arg or 'enum' in arg: return arg
        if (len(arg) == 0): return arg

        arg = arg.strip()

        if '*' in arg:
            if arg[0] == 'F':
                return 'struct ' + arg
            elif arg[0] in ['E']:
                return 'enum ' + arg
            elif arg[0] in ['U', 'A']:
                return 'class ' + arg

        return arg

    def render(self):
        if (self.type == 'FUNCTION'):
            try:
                parts = [ClassMember.transformArgToHeader(x.strip()) for x in self.args.split(',')]
            except Exception:
                parts = []

            ret = ''
            if self.cppType and not self.bare:
                ret += '\tUFUNCTION({mods})\n'.format(mods=self.mods)

            ret += '\t{static}{cppType}{name}({parts});\n'.format(
                static=('static ' if self.isStatic else ''),
                cppType=(str(self.cppType) + ' ' if self.cppType else ''),
                name=str(self.name),
                parts=', '.join(parts)
            )

            return ret
        elif self.type == 'PROPERTY':
            ret = ''
            if self.cppType[0] != 'F' and not self.bare:
                ret += '\tUPROPERTY({mods})\n'.format(mods=self.mods)

            arg = ClassMember.transformArgToHeader('{cppType} {name}'.format(cppType=self.cppType, name=self.name))

            ret += '\t{arg};\n'.format(arg=arg)
            return ret


    def __str__(self):
        return self.render()



def generateHeaderForCppFile(fn):
    members = []
    print(fn)

    tfn = fn.replace('Private', 'Public').replace('.cpp', '.h')
    if not os.path.isdir(os.path.dirname(tfn)): os.makedirs(os.path.dirname(tfn))

    try:
        if os.path.getmtime(fn) < os.path.getmtime(tfn):
            print('{fn} is not altered'.format(fn=fn))
            return False
    except Exception as ex:
        print("Error getting mtime: {ex}".format(ex=ex))

    className = re.search('([A-Z0-9a-z]+)\\.cpp', fn).group(1)

    extends = []
    isClassFile = False
    classMods = ''

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

                    m = re.match('blueprintEvent\\((?P<event>[^)]+)\\)', l)
                    if m:
                        members.append(ClassMember('FUNCTION', cppType='void', name=m.group(1), access='public', isConst=False, mods='BlueprintImplementableEvent'))

                    m = re.match('classMods\\((?P<mods>[^)]+)\\)', l)
                    if m:
                        classMods = m.group('mods')
    except Exception as ex:
        print("Error parsing CPP: " + str(ex))

    if not isClassFile: return None

    memberNames = [x.name for x in members]
    print(memberNames)

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

    print('extends ' + ', '.join(extends))

    defDependentClasses = list(extends)
    for mem in members:
        if mem.cppType and mem.cppType[0] == mem.cppType[0].upper() and not '*' in mem.cppType: defDependentClasses.append(mem.cppType)

    print('defDependentClasses={defDependentClasses}'.format(defDependentClasses=defDependentClasses))

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
            print("Can't find header for class {name}: {ex}".format(name=ext, ex=ex))
    ret += '#include "' + className[1:] + '.generated.h"\n'

    ret += '\n'
    ret += 'U' + classType.upper() + '(' + classMods + ')\n'
    ret += classType + ' ' + prjName.upper() + '_API ' + className + ' : public ' + ', '.join(extends) + '\n'
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
    print(ret)


    print(tfn)

    with open(tfn, 'w', newline='') as f:
        f.write(ret)

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
""".format(className=className, getterSetterImpls=getterSetterImpls)

    for header in depfinder.findDependentHeaders(fn):
        f.write('#include "{header}"\n'.format(header=header))

    with open(tfn, 'w', newline='') as f:
        f.write(pbt)



    return True