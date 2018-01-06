import time
import sys
import os
import re

engineDir = sys.argv[2]
prjDir = sys.argv[1]

headerMap = None

print("engineDir=" + engineDir + " prjFile=" + prjDir)

def fixCppFile(fn):
    includedFiles = []
    classes = []
    lastIncludePoint = -1

    with open(fn) as f:
        for l in f:
            for m in re.finditer('#include\s+"([^"]+?/([^/"]+))"', l):
                includedFiles.append(m.group(1))

            for m in re.finditer('[UAF][A-Z][a-z][A-Za-z0-9]+', l):
                classes.append(m.group(0))

    print(includedFiles)
    print(classes)

    for clazz in classes:
        findClassHeader(clazz)


def scanHeadersIn(dir):
    ret = {}
    for fn in os.listdir(dir):
        fullName = os.path.join(dir, fn)

        if os.path.isdir(fullName):
            for (k,v) in scanHeadersIn(fullName).items():
                ret[k] = v

        if fullName.endswith('.h'):
            with open(fullName) as f:
                for l in f:
                    for m in re.finditer('class[^:]+([UAF][A-Z][a-z][A-Za-z0-9]+)', l):
                        ret[m.group(1)] = fullName

    return ret


def findClassHeader(className):
    global headerMap

    if headerMap == None:
        headerMap = {}
        for (k,v) in scanHeadersIn(os.path.join(prjDir, 'Source')).items():
            headerMap[k] = v.replace(prjDir + '/Source/LandGrab/', '')

    print(headerMap)

def fixCppFilesIn(dir):
    for fn in os.listdir(dir):
        fullName = os.path.join(dir, fn)

        if os.path.isdir(fullName):
            fixCppFilesIn(fullName)

        if fullName.endswith('.cpp'):
            fixCppFile(fullName)

fixCppFilesIn(os.path.join(prjDir, 'Source'))

