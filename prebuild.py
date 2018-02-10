import time
import sys
import os
import re
import pickle
import shutil
import tempfile
import depfinder
import headergen

def main():
    targetName = sys.argv[1]
    engineDir = sys.argv[3]
    prjDir = sys.argv[2]

    prjName = targetName.replace('Editor', '')
    print("prjName=" + prjName + " targetName=" + targetName + " engineDir=" + engineDir + " prjFile=" + prjDir)

    def fixSourceFilesIn(dir):
        for fn in os.listdir(dir):
            fullName = os.path.join(dir, fn)

            if os.path.isdir(fullName):
                fixSourceFilesIn(fullName)

            if fullName.endswith('.cpp'):
                try:
                    headergen.generateHeaderForCppFile(fullName)
                except Exception as e:
                    print('Failed to generate for {fullName}: {e}'.format(fullName=fullName, e=e))

    fixSourceFilesIn(os.path.join(prjDir, 'Source'))

    print("prebuild complete")

main()