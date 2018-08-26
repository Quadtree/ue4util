import logging
import os

existing_content_cache = {}

def replaceIfModified(fn, content):
    if not os.path.exists(os.path.dirname(fn)):
        dir_name = os.path.dirname(fn)
        logging.info(f'Directory {dir_name} does not exist, creating')
        os.makedirs(dir_name)



    existingContent = None

    if fn in existing_content_cache:
        cur_mtime = os.path.getmtime(fn)
        old_mtime = existing_content_cache[fn]['mtime']

        if cur_mtime == old_mtime:
            existingContent = existing_content_cache[fn]['data']


    if existingContent == None:
        try:
            with open(fn, newline='\n') as f:
                existingContent = f.read()
        except FileNotFoundError:
            pass

        existing_content_cache[fn] = {
            'mtime': os.path.getmtime(fn),
            'data': existingContent
        }

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