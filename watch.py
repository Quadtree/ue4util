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
import json
import subprocess

def main():
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    project_file_name = None

    for f in os.listdir('.'):
        if f.endswith('.uproject'):
            project_file_name = f
            logging.info(f)

    project_file_contents = None

    with open(project_file_name) as f:
        project_file_contents = json.load(f)

    engine_version = project_file_contents['EngineAssociation']

    logging.info(f'engine_version={engine_version}')

    out = subprocess.check_output(['reg', 'query', f'HKLM\\SOFTWARE\\EpicGames\\Unreal Engine\\{engine_version}'])

    engine_path = None
    m = re.search('REG_SZ\\s+([^\\r\\n]+)', out.decode('utf8'))

    if m:
        engine_path = m.group(1) + '/Engine'

    logging.info(f'engine_path={engine_path}')

    curprj.targetName = project_file_name.replace('.uproject', '')
    curprj.engineDir = engine_path
    curprj.prjDir = '.'

    curprj.prjName = curprj.targetName
    logging.info("prjName=" + curprj.prjName + " targetName=" + curprj.targetName + " engineDir=" + curprj.engineDir + " prjFile=" + curprj.prjDir)

    last_fix = {}

    while(True):
        try:
            def fixSourceFilesIn(dir):
                for fn in os.listdir(dir):
                    fullName = os.path.join(dir, fn)

                    if os.path.isdir(fullName):
                        fixSourceFilesIn(fullName)

                    if fullName.endswith('.cpp'):
                        nmt = os.path.getmtime(fullName)
                        cmt = last_fix[fullName] if fullName in last_fix else None

                        if nmt != cmt:
                            headergen.generateHeaderForCppFile(fullName)
                            last_fix[fullName] = nmt

                time.sleep(0.5)

            fixSourceFilesIn(os.path.join(curprj.prjDir, 'Source'))
        except Exception as ex:
            print(f'Error while watching: {ex}')

main()

'''def main():
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)

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

main()'''