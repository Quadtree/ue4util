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

def find_highest_mtime_in(trg_dir):
    ret = 0

    for fn in os.listdir(trg_dir):
        full_name = os.path.join(trg_dir, fn)
        print(full_name)

        if os.path.isdir(full_name):
            print(f'desc {full_name}')
            ret = max(find_highest_mtime_in(full_name), ret)

        if full_name.endswith('.cpp') or full_name.endswith('.h'):
            try:
                ret = max(os.path.getmtime(full_name), ret)
            except Exception as ex:
                logging.error(f'Error getting mtime {ex}')

    return ret

def fixSourceFilesIn(dir):
    for fn in os.listdir(dir):
        fullName = os.path.join(dir, fn)

        if os.path.isdir(fullName):
            fixSourceFilesIn(fullName)

        if fullName.endswith('.cpp'):
            headergen.generateHeaderForCppFile(fullName)

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

    last_highest_mtime = 0

    while(True):
        start_time = time.perf_counter()
        try:
            depfinder.headerMap = None

            trg_dir = os.path.join(curprj.prjDir, 'Source')
            cur_highest_mtime = find_highest_mtime_in(trg_dir)
            print(cur_highest_mtime)

            if cur_highest_mtime > last_highest_mtime:
                logging.info(f'{cur_highest_mtime} > {last_highest_mtime}, doing run')
                fixSourceFilesIn(trg_dir)
                last_highest_mtime = cur_highest_mtime
        except Exception as ex:
            logging.error(f'Error while watching: {ex}')

        end_time = time.perf_counter()
        ms = int((end_time - start_time) * 1000)
        if ms >= 250: logging.info(f'Cycle took {ms}ms')
        time.sleep(0.5)

main()
