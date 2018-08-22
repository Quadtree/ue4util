import time
import sys
import os
import re
import pickle
import shutil
import tempfile
import depfinder
import curprj
import util
import logging
from classmember import ClassMember

def generate_enum_file_header(fn, enum_values, tfn, className, classMods):
    logging.info("Generating enum for " + fn + " -> " + tfn)

    if len(classMods) > 0: classMods += ', '
    classMods += 'BlueprintType'

    short_name = re.sub('[a-z]', '', className)

    out = '''#pragma once
#include "EngineMinimal.h"

UENUM(''' + classMods + ''')
enum class E''' + className + ''' : uint8
{
'''

    for v in enum_values:
        out += f'\t{short_name}_{v},\n'

    out += '};\n'

    util.replaceIfModified(tfn, out)

    tfn = fn.replace('Private', 'Public').replace('.cpp', '.ac.h')

    pbt = """
#define enumValue(...)
#define classMods(...)
"""

    util.replaceIfModified(tfn, pbt)

    return True