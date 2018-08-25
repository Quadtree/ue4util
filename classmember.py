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

class ClassMember:
    def __init__(self, typ, cppType, name, access, isConst, className = None, mods = None, args = None, bare=False):
        self.type = str(typ)
        self.cppType = cppType
        self.name = name
        self.isConst = isConst
        self.bare = bare
        self.isStatic = False
        self.access = access
        self.isOverride = False

        if not mods: mods = ''

        modList = []
        if mods: modList = [x.strip() for x in mods.split(' ')]

        logging.debug('modList=' + str(modList))

        for accessLevel in ['privateGS', 'protectedGS', 'publicGS', 'private', 'protected', 'public']:
            if accessLevel in modList:
                self.access = accessLevel
                modList.remove(accessLevel)
                break

        logging.debug('access=' + self.access + ',type=' + self.type)

        if 'bare' in modList:
            modList.remove('bare')
            self.bare = True

        if 'static' in modList:
            modList.remove('static')
            self.isStatic = True

        self.generateGetter = 'G' in self.access
        self.generateSetter = 'S' in self.access
        self.access = self.access.replace('G', '').replace('S', '')

        if self.type == 'PROPERTY':
            if 'UDataTable' not in self.cppType:
                modList.append('SaveGame')

            if self.access == 'public':
                modList.append('BlueprintReadWrite')
            else:
                logging.debug("NOT PUBLIC '{access}' != 'public'".format(access=self.access))

            # Currently, just assume that everything can be changed in the editor
            if ('Component' in cppType):
                modList.append('VisibleAnywhere')
            else:
                modList.append('EditAnywhere')

        logging.debug('modList=' + str(modList))

        if self.type == 'FUNCTION':
            if self.access == 'public' and name.startswith('Get') and not (set(modList) & set(['BlueprintCallable', 'BlueprintPure', 'BlueprintImplementableEvent'])):
                modList.append('BlueprintPure')

            if not (set(['BlueprintImplementableEvent', 'BlueprintPure']) & set(modList)):
                modList.append('BlueprintCallable')

            if (self.access == 'private' and 'BlueprintCallable' in modList):
                modList.remove('BlueprintCallable')

        self.mods = ', '.join(modList)
        self.args = args
        self.className = className

    def createFromLine(line):
        m = re.match("prop\\(((?P<mods>[^)]+?)\\s+)?(?P<typ>[A-Za-z0-9]+(<[^>]+>)?\\s*\\*?)\\s+(?P<name>[A-Za-z0-9*]+)\\)", line)
        if (m):
            return ClassMember(
                typ='PROPERTY',
                cppType=m.group('typ'),
                name=m.group('name'),
                access='privateGS',
                isConst=False,
                className='Class',
                mods=m.group('mods'),
                args=None,
                bare=False)

        m = re.search("(mods\\((?P<mods>[^)]+)\\)\\s+)?((?P<retTyp>[A-Za-z0-9 &*<>,]+)?\\s+)?fun::(?P<funcName>[A-Za-z0-9]+)\\s*\\((?P<args>[^)]*)\\)", line)
        if (m):
            logging.debug('cppType=' + str(m.group('retTyp')))
            return ClassMember(
                typ='FUNCTION',
                cppType=m.group('retTyp'),
                name=m.group('funcName'),
                access='public',
                isConst=False,
                className='Class',
                mods=m.group('mods'),
                args=m.group('args'),
                bare=False)

    def transformArgToHeader(arg):
        if 'class' in arg or 'struct' in arg or 'enum' in arg: return arg
        if (len(arg) == 0): return arg

        arg = arg.strip()

        if '*' in arg:
            if arg[0] == 'F':
                return 'struct ' + arg
            elif arg[0] in ['E']:
                return 'enum ' + arg
            elif arg[0] in ['U', 'A']:
                return 'class ' + arg

        return arg

    def render(self):
        if (self.type == 'FUNCTION'):
            if self.isOverride:
                self.bare = True

            try:
                parts = [ClassMember.transformArgToHeader(x.strip()) for x in self.args.split(',')]
            except Exception:
                parts = []

            ret = ''
            if self.cppType and not self.bare:
                ret += '\tUFUNCTION({mods})\n'.format(mods=self.mods)

            typeString = ClassMember.transformArgToHeader(str(self.cppType) + ' ' if self.cppType else '')
            if typeString: typeString += ' '

            override = ''
            if self.isOverride:
                override = ' override'

            ret += '\t{static}{cppType}{name}({parts}){override};\n'.format(
                static=('static ' if self.isStatic else ''),
                cppType=typeString,
                name=str(self.name),
                parts=', '.join(parts),
                override=override
            )

            return ret
        elif self.type == 'PROPERTY':
            mods = self.mods
            if self.generateGetter: mods += f', BlueprintGetter=Get{self.name}'
            if self.generateSetter: mods += f', BlueprintSetter=Set{self.name}'

            ret = ''
            if not self.bare:
                ret += f'\tUPROPERTY({mods})\n'

            arg = ClassMember.transformArgToHeader('{cppType} {name}'.format(cppType=self.cppType, name=self.name))

            ret += '\t{arg};\n'.format(arg=arg)
            return ret


    def __str__(self):
        return self.render()