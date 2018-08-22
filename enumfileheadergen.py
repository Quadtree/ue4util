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

def generate_class_file_header(fn, enum_values, tfn, className, classMods):

    tfn = fn.replace('Private', 'Public').replace('.cpp', '.ac.h')

    pbt = """
#define enumValue(...)
#define classMods(...)
"""

    util.replaceIfModified(tfn, pbt)

    return True