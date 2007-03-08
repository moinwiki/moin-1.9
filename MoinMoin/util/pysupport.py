# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Supporting function for Python magic

    @copyright: 2002 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

#############################################################################
### Module import / Plugins
#############################################################################

def isImportable(module):
    """ Check whether a certain module is available.
    """
    try:
        __import__(module)
        return 1
    except ImportError:
        return 0


def getPackageModules(packagefile):
    """ Return a list of modules for a package, omitting any modules
        starting with an underscore.
    """
    import os, re

    packagedir = os.path.dirname(packagefile)

    in_plugin_dir = lambda dir, ops=os.path.split: ops(ops(dir)[0])[1] == "plugin"

    moinmodule = __import__('MoinMoin')

    # Is it in a .zip file?
    if not in_plugin_dir(packagedir) and hasattr(moinmodule, '__loader__'):
        pyre = re.compile(r"^([^_].*)\.py(?:c|o)$")
        zipfiles = moinmodule.__loader__._files
        dirlist = [file[0].replace(r'/', '\\').split('\\')[-1]
                   for file in zipfiles.values() if packagedir in file[0]]
    else:
        pyre = re.compile(r"^([^_].*)\.py$")
        dirlist = os.listdir(packagedir)

    pyfiles = filter(None, map(pyre.match, dirlist))
    modules = map(lambda x: x.group(1), pyfiles)

    modules.sort()
    return modules


def importName(modulename, name):
    """ Import name dynamically from module

    Used to do dynamic import of modules and names that you know their
    names only in runtime.

    Any error raised here must be handled by the caller.
    
    @param modulename: full qualified mudule name, e.g. x.y.z
    @param name: name to import from modulename
    @rtype: any object
    @return: name from module
    """
    module = __import__(modulename, globals(), {}, [name])
    return getattr(module, name)


def makeThreadSafe(function, lock=None):
    """ Call with a function you want to make thread safe

    Call without lock to make the function thread safe using one lock per
    function. Call with existing lock object if you want to make several
    functions use same lock, e.g. all functions that change same data
    structure.

    @param function: function to make thread safe
    @param lock: threading.Lock instance or None
    @rtype: function
    @return: function decorated with locking
    """
    if lock is None:
        import threading
        lock = threading.Lock()

    def decorated(*args, **kw):
        lock.acquire()
        try:
            return function(*args, **kw)
        finally:
            lock.release()

    return decorated
