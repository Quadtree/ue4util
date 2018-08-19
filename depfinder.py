import os
import re
import curprj
import logging
import pickle

headerMap = None

def scanHeadersIn(dir):
    ret = {}
    for fn in os.listdir(dir):
        fullName = os.path.join(dir, fn)

        if os.path.isdir(fullName):
            for (k,v) in scanHeadersIn(fullName).items():
                ret[k] = v
        try:
            if fullName.endswith('.h'):
                with open(fullName) as f:
                    for l in f:
                        if ';' not in l:
                            for m in re.finditer('^(?:class|struct|enum)[^:]*\s([A-Z][A-Za-z0-9]+)\s', l):
                                ret[m.group(1)] = fullName.replace('\\', '/')
        except Exception:
            logging.warning("Error")

    return ret


def findClassHeader(className):
    global headerMap

    if headerMap == None:
        headerMap = {}
        for (k,v) in scanHeadersIn(os.path.join(curprj.prjDir, 'Source')).items():
            m = re.match('.+' + curprj.prjName + '(\\\\|/)(.+)', v)
            if m:
                headerMap[k] = m.group(2)

        logging.info(headerMap)

        cacheFileName = os.path.join(curprj.prjDir, '.prebuild.cache')
        engineMap = {}

        try:
            with open(cacheFileName, 'rb') as f: engineMap = pickle.load(f)
        except Exception as ex:
            logging.info("Rebuilding engine header cache because " + str(ex))
            for (k,v) in scanHeadersIn(os.path.join(curprj.engineDir, 'Source')).items():
                m = re.match('.+(Public|Classes)/(.+)', v)

                if m:
                    engineMap[k] = m.group(2)

            with open(cacheFileName, 'wb') as f:
                pickle.dump(engineMap, f)

            logging.info("Completed recreation of cache file")

        for (k,v) in engineMap.items():
            headerMap[k] = v

    if className in headerMap:
        return headerMap[className]

    return None

def findDependentHeaders(fn, class_name_filter='[A-Z][A-Za-z0-9]+'):
    includedFiles = []
    classes = []
    lastIncludeLine = -1

    foundLogStatement = False
    foundWindowsLineEndings = False
    foundTrailingWhitespace = False
    isCppFile = fn.endswith('.cpp')

    fns = []
    fns.append(fn)

    for theFn in fns:
        try:
            with open(theFn, newline='') as f:
                ln = 0
                for l in f:
                    if isCppFile:
                        for m in re.finditer('#include\s+"([^"]+?/?([^/"]+))"', l):
                            includedFiles.append(m.group(1))
                            lastIncludeLine = ln

                        for m in re.finditer(class_name_filter, l):
                            classes.append(m.group(0))

                        if 'UE_LOG' in l: foundLogStatement = True

                    if '\r\n' in l: foundWindowsLineEndings = True
                    if re.match('[\\t ]\\s*$', l):
                        foundTrailingWhitespace = True
                        logging.debug("Found trailing whitespace in " + fn)


                    ln += 1
        except Exception as ex:
            logging.warning("Header loader error? " + str(ex))

    headersToAdd = []

    if foundLogStatement and (curprj.prjName + '.h'):
        headersToAdd.append(curprj.prjName + '.h')

    for clazz in classes:
        header = findClassHeader(clazz)

        if header and header not in headersToAdd and header:
            headersToAdd.append(header)

    return headersToAdd