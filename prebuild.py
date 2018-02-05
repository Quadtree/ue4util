import time
import sys
import os
import re
import pickle
import shutil
import tempfile

class ClassMember:
    def __init__(self, line):
        self.type = None

        print("LA " + line)
        m = re.match("//@ ([A-Za-z0-9]+)\\* ([A-Za-z0-9]+)", line)
        if (m):
            pass

        m = re.search("\\s*([A-Za-z0-9]+)\\s*\\*\\s*([A-Za-z0-9]+)::([A-Za-z0-9]+)\\s*\\(([^)]*)\\)", line)
        if (m):
            print(m)

def findMembersInCppFile(fn):
    members = []
    print(fn)

    try:
        with open(fn) as f:
            for l in f:
                if (re.match("\\S.+", l)):
                    newMember = ClassMember(l)

                    if newMember.type != None:
                        members.append(newMember)
    except Exception as ex:
        print("Error parsing CPP: " + str(ex))


    print(members)
    sys.exit()
    return members


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
        fns.append(fn.replace('.cpp', '.h'))

        findMembersInCppFile(fn)




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

    if foundLogStatement and (prjName + '.h') not in includedFiles:
        headersToAdd.append(prjName + '.h')

    for clazz in classes:
        header = findClassHeader(clazz)

        if header and header not in headersToAdd and header not in includedFiles:
            headersToAdd.append(header)

    if headersToAdd or foundWindowsLineEndings or foundTrailingWhitespace:
        print("Headers to add to " + fn + " = " + str(headersToAdd))

        bfn = os.path.join(tempfile.gettempdir(), os.path.basename(fn) + '.prebuild.bkp')
        try:
            os.remove(bfn)
        except Exception: pass
        shutil.move(fn, bfn)

        try:
            with open(bfn, 'r') as fr:
                with open(fn, 'w', newline='\n') as fw:
                    ln = 0

                    for l in fr:
                        if ln == lastIncludeLine + 1:
                            for header in headersToAdd:
                                fw.write('#include "' + header + '"\n')

                        fw.write(re.sub('\\s+$', '', l) + '\n')
                        ln += 1
        except Exception as ex:
            print("Error saving " + str(ex))

            try:
                os.remove(fn)
            except Exception: pass

            shutil.copy(bfn, fn)


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