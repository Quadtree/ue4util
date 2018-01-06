import time
import sys
import os
import re
import pickle

engineDir = sys.argv[2]
prjDir = sys.argv[1]

headerMap = None

print("engineDir=" + engineDir + " prjFile=" + prjDir)

def fixCppFile(fn):
    includedFiles = []
    classes = []
    lastIncludeLine = -1

    with open(fn) as f:
        ln = 0
        for l in f:
            for m in re.finditer('#include\s+"([^"]+?/([^/"]+))"', l):
                includedFiles.append(m.group(1))
                lastIncludeLine = ln

            for m in re.finditer('[UAF][A-Z][a-z][A-Za-z0-9]+', l):
                classes.append(m.group(0))

            ln += 1

    #print(includedFiles)
    #print(classes)

    headersToAdd = []

    for clazz in classes:
        header = findClassHeader(clazz)

        if header and header not in headersToAdd and header not in includedFiles:
            headersToAdd.append(header)

    if headersToAdd:
        print("Headers to add to " + fn + " = " + str(headersToAdd))


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
                        for m in re.finditer('class[^:]+([UAF][A-Z][a-z][A-Za-z0-9]+)', l):
                            ret[m.group(1)] = fullName
        except Exception:
            print("Error")

    return ret


def findClassHeader(className):
    global headerMap

    if headerMap == None:
        headerMap = {}
        for (k,v) in scanHeadersIn(os.path.join(prjDir, 'Source')).items():
            # TODO: Fix me
            headerMap[k] = v.replace(prjDir + '/Source/LandGrab/', '')

        cacheFileName = os.path.join(prjDir, '.prebuildcache')
        engineMap = {}

        try:
            with open(cacheFileName, 'rb') as f: engineMap = pickle.load(f)
        except Exception as ex:
            print("Rebuilding engine header cache because " + str(ex))
            for (k,v) in scanHeadersIn(os.path.join(engineDir, 'Source')).items():
                m = re.match('.+Public/(.+)', v)

                if m:
                    engineMap[k] = m.group(1)

            with open(cacheFileName, 'wb') as f:
                pickle.dump(engineMap, f)

        for (k,v) in engineMap.items():
            headerMap[k] = v

    if className in headerMap:
        return headerMap[className]

    return None

def fixCppFilesIn(dir):
    for fn in os.listdir(dir):
        fullName = os.path.join(dir, fn)

        if os.path.isdir(fullName):
            fixCppFilesIn(fullName)

        if fullName.endswith('.cpp'):
            fixCppFile(fullName)

fixCppFilesIn(os.path.join(prjDir, 'Source'))

