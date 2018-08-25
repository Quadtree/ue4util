import logging
import os

def replaceIfModified(fn, content):
    if not os.path.exists(os.path.dirname(fn)):
        dir_name = os.path.dirname(fn)
        logging.info(f'Directory {dir_name} does not exist, creating')
        os.makedirs(dir_name)

    existingContent = ''
    try:
        with open(fn, newline='\n') as f:
            existingContent = f.read()
    except FileNotFoundError:
        pass

    if existingContent != content:
        with open(fn, 'w', newline='\n') as f:
            f.write(content)

        logging.info("Wrote new content to file %s", fn)
    else:
        logging.debug("File %s is unchanged", fn)

def split_list(list_str):
    parts = list_str.split(' ')

    parts_stripped = map(lambda s: s.strip(', '), parts)

    return filter(lambda s: len(str(s)) > 0, parts_stripped)

def join_list(list):
    return ', '.join(list)