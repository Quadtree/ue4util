import logging

def replaceIfModified(fn, content):
    existingContent = ''
    with open(fn, newline='\n') as f:
        existingContent = f.read()

    if existingContent != content:
        with open(fn, 'w', newline='\n') as f:
            f.write(content)

        logging.info("Wrote new content to file %s", fn)
    else:
        logging.info("File %s is unchanged", fn)