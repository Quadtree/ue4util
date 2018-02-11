import time
import sys
import os
import re
import pickle
import shutil
import tempfile
import depfinder
import headergen
import curprj
import logging

def main():
    logging.basicConfig(level=logging.INFO)

    curprj.targetName = sys.argv[1]
    curprj.engineDir = sys.argv[3]
    curprj.prjDir = sys.argv[2]

    curprj.prjName = curprj.targetName.replace('Editor', '')
    logging.info("prjName=" + curprj.prjName + " targetName=" + curprj.targetName + " engineDir=" + curprj.engineDir + " prjFile=" + curprj.prjDir)

    def fixSourceFilesIn(dir):
        for fn in os.listdir(dir):
            fullName = os.path.join(dir, fn)

            if os.path.isdir(fullName):
                fixSourceFilesIn(fullName)

            if fullName.endswith('.cpp'):
                headergen.generateHeaderForCppFile(fullName)

    fixSourceFilesIn(os.path.join(curprj.prjDir, 'Source'))

    logging.info("prebuild complete")

main()