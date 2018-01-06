import time
import sys
import os
import re

engineDir = sys.argv[2]
prjDir = sys.argv[1]

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


def scanHeadersIn(dir):
    for fn in os.listdir(dir):
        fullName = os.path.join(dir, fn)

        if os.path.isdir(fullName):
            fixCppFilesIn(fullName)

        if fullName.endswith('.h'):
            with open(fn) as f:
                for l in f:
                    for m in re.finditer('class[^:]+([UAF][A-Z][a-z][A-Za-z0-9]+)', l):
                        print("Found: " + m.group(1))


def findClassHeader(className):
    scanHeadersIn(engineDir)

def fixCppFilesIn(dir):
    for fn in os.listdir(dir):
        fullName = os.path.join(dir, fn)

        if os.path.isdir(fullName):
            fixCppFilesIn(fullName)

        if fullName.endswith('.cpp'):
            fixCppFile(fullName)

fixCppFilesIn(os.path.join(prjDir, 'Source'))

