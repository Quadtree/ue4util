import time
import sys
import os
import re
import pickle
import shutil
import tempfile

# To add:
# Fields
# Header generation
# Getter/setter generation

class ClassMember:
    def __init__(self, typ, cppType, name, access, isConst, className = None, mods = None, args = None):
        self.type = str(typ)
        self.cppType = cppType
        self.name = name
        self.isConst = isConst
        self.generateGetter = 'G' in access
        self.generateSetter = 'S' in access
        self.access = access.replace('G', '').replace('S', '')

        if not mods: mods = ''

        modList = []
        if mods: modList = [x.strip() for x in mods.split(' ')]

        if self.type == 'PROPERTY':
            modList.append('SaveGame')

        if self.type == 'FUNCTION':
            if not 'BlueprintPure' in mods:
                modList.append('BlueprintCallable')

            if (self.access == 'private' and 'BlueprintCallable' in modList):
                modList.remove('BlueprintCallable')


        self.mods = ', '.join(modList)
        self.args = args
        self.className = className





    def createFromLine(line):
        m = re.match("prop\\(((?P<protLevel>private|public|protected)\\s+)?(?P<typ>[A-Za-z0-9*]+)\\s+(?P<name>[A-Za-z0-9*]+)\\)", line)
        if (m):
            return ClassMember(
                typ='PROPERTY',
                cppType=m.group('typ'),
                name=m.group('name'),
                access=m.group('protLevel') if m.group('protLevel') else 'privateGS',
                isConst=False,
                className='Class',
                mods=None,
                args=None)

        m = re.search("(?P<protLevel>private|public|protected)?\\s*((?P<retTyp>[A-Za-z0-9 *]+)?\\s+)?fun::(?P<funcName>[A-Za-z0-9]+)\\s*\\((?P<args>[^)]*)\\)(\\s+mods\\((?P<mods>[^)]+)\\))?", line)
        if (m):
            print('cppType=' + str(m.group('retTyp')))
            return ClassMember(
                typ='FUNCTION',
                cppType=m.group('retTyp'),
                name=m.group('funcName'),
                access=m.group('protLevel') if m.group('protLevel') else 'public',
                isConst=False,
                className='Class',
                mods=m.group('mods'),
                args=m.group('args'))

    def transformArgToHeader(arg):
        if 'class' in arg or 'struct' in arg: return arg

        if (len(arg) == 0): return arg

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

            return (('\tUFUNCTION(' + str(self.mods) + ')\n') if self.cppType else '') + '\t' + (str(self.cppType) + ' ' if self.cppType else '') + str(self.name) + '(' + ', '.join(parts) + ')' + (' const' if self.isConst else '') + ';\n'
        elif self.type == 'PROPERTY':
            return '\tUPROPERTY({mods})\n\t{cppType} {name};\n'.format(mods=self.mods, cppType=self.cppType, name=self.name)


    def __str__(self):
        return self.render()



def findMembersInCppFile(fn):
    members = []
    print(fn)

    tfn = fn.replace('Private', 'Public').replace('.cpp', '.h')

    """try:
        if os.path.getmtime(fn) < os.path.getmtime(tfn):
            print('{fn} is not altered'.format(fn=fn))
            return False
    except Exception as ex:
        print("Error getting mtime: {ex}".format(ex=ex))"""

    className = re.search('([A-Z0-9a-z]+)\\.cpp', fn).group(1)

    extends = []
    isClassFile = False

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

                    m = re.match("//@\\s+extends\\s+([A-Za-z0-9]+)", l)
                    if m:
                        extends = [x.strip() for x in m.group(1).split(' ')]
    except Exception as ex:
        print("Error parsing CPP: " + str(ex))

    if not isClassFile: return None

    memberNames = [x.name for x in members]
    print(memberNames)

    getterSetterImpls = ''

    for mem in members:
        if mem.generateGetter:
            getterName = 'Get' + mem.name
            members.append(ClassMember('FUNCTION', cppType=mem.cppType, name=getterName, access='public', isConst=False))
            if not getterName in memberNames:
                getterSetterImpls += '{retTyp} {className}::{getterName}(){{ return {name}; }}\n'.format(retTyp=mem.cppType, className=className, getterName=getterName, name=mem.name)


    print('extends ' + ', '.join(extends))

    if className[0] == 'F':
        classType = 'struct'
    elif className[0] == 'E':
        classType = 'enum'
    else:
        classType = 'class'

    ret = '#pragma once\n\n'
    ret += '#include "EngineMinimal.h"\n'
    for ext in extends:
        ret += '#include "' + findClassHeader(ext) + '"\n'
    ret += '#include "' + className[1:] + '.generated.h"\n'

    ret += '\n'
    ret += 'U' + classType.upper() + '()\n'
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

    tfn = fn.replace('Private', 'Public').replace('.cpp', '.prebuild.h')

    pbt = """
#define mods(x)
#define public
#define private
#define protected
#define prop(x)
#define extends(x)
#define fun         {className}
{getterSetterImpls}
""".format(className=className, getterSetterImpls=getterSetterImpls)


    with open(tfn, 'w', newline='') as f:
        f.write(pbt)

    return True


targetName = sys.argv[1]
engineDir = sys.argv[3]
prjDir = sys.argv[2]

prjName = targetName.replace('Editor', '')

headerMap = None

print("prjName=" + prjName + " targetName=" + targetName + " engineDir=" + engineDir + " prjFile=" + prjDir)

def fixSourceFile(fn):
    includedFiles = []
    classes = []
    lastIncludeLine = -1

    foundLogStatement = False
    foundWindowsLineEndings = False
    foundTrailingWhitespace = False
    isCppFile = fn.endswith('.cpp')

    fns = []
    if isCppFile:
        if not findMembersInCppFile(fn):
            return

    fns.append(fn)

    for theFn in fns:
        try:
            with open(theFn, newline='') as f:
                ln = 0
                for l in f:
                    if isCppFile:
                        for m in re.finditer('#include\s+"([^"]+?/?([^/"]+))"', l):
                            includedFiles.append(m.group(1))
                            lastIncludeLine = ln

                        for m in re.finditer('[A-Z][A-Za-z0-9]+', l):
                            classes.append(m.group(0))

                        if 'UE_LOG' in l: foundLogStatement = True

                    if '\r\n' in l: foundWindowsLineEndings = True
                    if re.match('[\\t ]\\s*$', l):
                        foundTrailingWhitespace = True
                        print("Found trailing whitespace in " + fn)


                    ln += 1
        except Exception as ex:
            print("Header loader error? " + str(ex))

    #print(includedFiles)
    #print(classes)

    headersToAdd = []

    if foundLogStatement and (prjName + '.h'):
        headersToAdd.append(prjName + '.h')

    for clazz in classes:
        header = findClassHeader(clazz)

        if header and header not in headersToAdd and header:
            headersToAdd.append(header)

    if headersToAdd:
        tfn = fn.replace('Private', 'Public').replace('.cpp', '.prebuild.h')

        if (os.path.exists(tfn)):
            with open(tfn, 'a', newline='') as f:
                for header in headersToAdd:
                    f.write('#include "{header}"\n'.format(header=header))


def scanHeadersIn(dir):
    ret = {}
    for fn in os.listdir(dir):
        fullName = os.path.join(dir, fn)

        if os.path.isdir(fullName):
            for (k,v) in scanHeadersIn(fullName).items():
                ret[k] = v
        try:
            if fullName.endswith('.h'):
                with open(fullName) as f:
                    for l in f:
                        if ';' not in l:
                            for m in re.finditer('^class[^:]*\s([A-Z][A-Za-z0-9]+)\s', l):
                                ret[m.group(1)] = fullName.replace('\\', '/')
        except Exception:
            print("Error")

    return ret


def findClassHeader(className):
    global headerMap

    if headerMap == None:
        headerMap = {}
        for (k,v) in scanHeadersIn(os.path.join(prjDir, 'Source')).items():
            m = re.match('.+' + prjName + '(\\\\|/)(.+)', v)
            if m:
                headerMap[k] = m.group(2)

        print(headerMap)

        cacheFileName = os.path.join(prjDir, '.prebuild.cache')
        engineMap = {}

        try:
            with open(cacheFileName, 'rb') as f: engineMap = pickle.load(f)
        except Exception as ex:
            print("Rebuilding engine header cache because " + str(ex))
            for (k,v) in scanHeadersIn(os.path.join(engineDir, 'Source')).items():
                m = re.match('.+(Public|Classes)/(.+)', v)

                if m:
                    engineMap[k] = m.group(2)

            with open(cacheFileName, 'wb') as f:
                pickle.dump(engineMap, f)

        for (k,v) in engineMap.items():
            headerMap[k] = v

    if className in headerMap:
        return headerMap[className]

    return None

def fixSourceFilesIn(dir):
    for fn in os.listdir(dir):
        fullName = os.path.join(dir, fn)

        if os.path.isdir(fullName):
            fixSourceFilesIn(fullName)

        if fullName.endswith('.cpp') or fullName.endswith('.h'):
            fixSourceFile(fullName)

fixSourceFilesIn(os.path.join(prjDir, 'Source'))

print("prebuild complete")