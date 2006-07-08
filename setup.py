#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
    MoinMoin installer

    @copyright: 2001-2005 by J�rgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import glob, os, string, sys

import distutils
from distutils.core import setup
from distutils.command.build_scripts import build_scripts

from MoinMoin.version import release, revision

# we need this for distutils from python 2.3 compatibility, python 2.4 has the
# 'package_data' keyword to the 'setup' function to install data in packages 
# see http://wiki.python.org/moin/DistutilsInstallDataScattered
from distutils.command.install_data import install_data
class smart_install_data(install_data):
    def run(self):
        i18n_data_files = [(target, files) for (target, files) in self.data_files if target.startswith('MoinMoin/i18n')]
        share_data_files = [(target, files) for (target, files) in self.data_files if target.startswith('share/moin')]
        # first install the share/moin stuff:
        self.data_files = share_data_files
        install_data.run(self)
        # now we need to install the *.po files to the package dir:
        # need to change self.install_dir to the library dir
        install_cmd = self.get_finalized_command('install')
        self.install_dir = getattr(install_cmd, 'install_lib')
        self.data_files = i18n_data_files
        return install_data.run(self)

#############################################################################
### Helpers
#############################################################################

def isbad(name):
    """ Whether name should not be installed """
    return (name.startswith('.') or
            name.startswith('#') or
            name.endswith('.pickle') or
            name == 'CVS')

def isgood(name):
    """ Whether name should be installed """
    return not isbad(name)

def makeDataFiles(prefix, dir):
    """ Create distutils data_files structure from dir

    distutil will copy all file rooted under dir into prefix, excluding
    dir itself, just like 'ditto src dst' works, and unlike 'cp -r src
    dst, which copy src into dst'.

    Typical usage:
        # install the contents of 'wiki' under sys.prefix+'share/moin'
        data_files = makeDataFiles('share/moin', 'wiki')

    For this directory structure:
        root
            file1
            file2
            dir
                file
                subdir
                    file

    makeDataFiles('prefix', 'root')  will create this distutil data_files structure:
        [('prefix', ['file1', 'file2']),
         ('prefix/dir', ['file']),
         ('prefix/dir/subdir', ['file'])]

    """
    # Strip 'dir/' from of path before joining with prefix
    dir = dir.rstrip('/')
    strip = len(dir) + 1
    found = []
    os.path.walk(dir, visit, (prefix, strip, found))
    return found

def visit((prefix, strip, found), dirname, names):
    """ Visit directory, create distutil tuple

    Add distutil tuple for each directory using this format:
        (destination, [dirname/file1, dirname/file2, ...])

    distutil will copy later file1, file2, ... info destination.
    """
    files = []
    # Iterate over a copy of names, modify names
    for name in names[:]:
        path = os.path.join(dirname, name)
        # Ignore directories -  we will visit later
        if os.path.isdir(path):
            # Remove directories we don't want to visit later
            if isbad(name):
                names.remove(name)
            continue
        elif isgood(name):
            files.append(path)
    destination = os.path.join(prefix, dirname[strip:])
    found.append((destination, files))


#############################################################################
### Build script files
#############################################################################

class build_scripts_create(build_scripts):
    """ Overload the build_scripts command and create the scripts
        from scratch, depending on the target platform.

        You have to define the name of your package in an inherited
        class (due to the delayed instantiation of command classes
        in distutils, this cannot be passed to __init__).

        The scripts are created in an uniform scheme: they start the
        run() function in the module

            <packagename>.script.<mangled_scriptname>

        The mangling of script names replaces '-' and '/' characters
        with '-' and '.', so that they are valid module paths. 
    """
    package_name = None

    def copy_scripts(self):
        """ Create each script listed in 'self.scripts'
        """
        if not self.package_name:
            raise Exception("You have to inherit build_scripts_create and"
                " provide a package name")

        to_module = string.maketrans('-/', '_.')

        self.mkpath(self.build_dir)
        for script in self.scripts:
            outfile = os.path.join(self.build_dir, os.path.basename(script))

            #if not self.force and not newer(script, outfile):
            #    self.announce("not copying %s (up-to-date)" % script)
            #    continue

            if self.dry_run:
                self.announce("would create %s" % outfile)
                continue

            module = os.path.splitext(os.path.basename(script))[0]
            module = string.translate(module, to_module)
            script_vars = {
                'python': os.path.normpath(sys.executable),
                'package': self.package_name,
                'module': module,
                'package_location': '/usr/lib/python/site-packages', # FIXME
            }

            self.announce("creating %s" % outfile)
            file = open(outfile, 'w')

            try:
                if sys.platform == "win32":
                    file.write('@echo off\n'
                        'if NOT "%%_4ver%%" == "" %(python)s -c "from %(package)s.script.%(module)s import run; run()" %%$\n'
                        'if     "%%_4ver%%" == "" %(python)s -c "from %(package)s.script.%(module)s import run; run()" %%*\n'
                        % script_vars)
                else:
                    file.write("#! %(python)s\n"
                        "#Fix and uncomment those 2 lines if your moin command doesn't find the MoinMoin package:\n"
                        "#import sys\n"
                        "#sys.path.insert(0, '%(package_location)s')\n"
                        "from %(package)s.script.%(module)s import run\n"
                        "run()\n"
                        % script_vars)
            finally:
                file.close()
                os.chmod(outfile, 0755)


class build_scripts_moin(build_scripts_create):
    package_name = 'MoinMoin'


def scriptname(path):
    """ Helper for building a list of script names from a list of
        module files.
    """
    script = os.path.splitext(os.path.basename(path))[0]
    script = string.replace(script, '_', '-')
    if sys.platform == "win32":
        script = script + ".bat"
    return script

# build list of scripts from their implementation modules
moin_scripts = map(scriptname, glob.glob('MoinMoin/script/[!_]*.py'))


#############################################################################
### Call setup()
#############################################################################

setup_args = {
    'name': "moin",
    'version': release,
    'description': "MoinMoin %s.%s is a Python clone of WikiWiki" % (release, revision),
    'author': "J�rgen Hermann",
    'author_email': "jh@web.de",
    'url': "http://moinmoin.wikiwikiweb.de/",
    'license': "GNU GPL",
    'long_description': """
A WikiWikiWeb is a collaborative hypertext environment, with an
emphasis on easy access to and modification of information. MoinMoin
is a Python WikiClone that allows you to easily set up your own wiki,
only requiring a Python installation. 
""",
    'packages': [
        'MoinMoin',
        'MoinMoin.action',
        'MoinMoin.auth',
        'MoinMoin.converter',
        'MoinMoin.filter',
        'MoinMoin.formatter',
        'MoinMoin.i18n',
        'MoinMoin.i18n.tools',
        'MoinMoin.logfile',
        'MoinMoin.macro',
        'MoinMoin.mail',
        'MoinMoin.parser',
        'MoinMoin.request',
        'MoinMoin.script',
        'MoinMoin.script.account',
        'MoinMoin.script.cli',
        'MoinMoin.script.export',
        'MoinMoin.script.import',
        'MoinMoin.script.index',
        'MoinMoin.script.maint',
        'MoinMoin.script.migration',
        'MoinMoin.script.old',
        'MoinMoin.script.old.migration',
        'MoinMoin.script.old.xmlrpc-tools',
        'MoinMoin.security',
        'MoinMoin.server',
        'MoinMoin.stats',
        'MoinMoin.support',
        'MoinMoin.support.xapwrap',
        'MoinMoin.theme',
        'MoinMoin.util',
        'MoinMoin.widget',
        'MoinMoin.wikixml',
        'MoinMoin.xmlrpc',

        # if we get *massive* amounts of test, this should probably be left out
        'MoinMoin._tests',
    ],

    # We can use package_* instead of the smart_install_data hack when we
    # require Python 2.4.
    #'package_dir': { 'MoinMoin.i18n': 'MoinMoin/i18n', },
    #'package_data': { 'MoinMoin.i18n': ['README', 'Makefile', 'MoinMoin.pot', 'POTFILES.in',
    #                                    '*.po',
    #                                    'tools/*',], },

    # Override certain command classes with our own ones
    'cmdclass': {
        'build_scripts': build_scripts_moin,
        'install_data': smart_install_data, # hack needed for 2.3
    },

    'scripts': moin_scripts,

    # This copies the contents of wiki dir under sys.prefix/share/moin
    # Do not put files that should not be installed in the wiki dir, or
    # clean the dir before you make the distribution tarball.
    'data_files': makeDataFiles('share/moin', 'wiki') + makeDataFiles('MoinMoin/i18n', 'MoinMoin/i18n')
}

if hasattr(distutils.dist.DistributionMetadata, 'get_keywords'):
    setup_args['keywords'] = "wiki web"

if hasattr(distutils.dist.DistributionMetadata, 'get_platforms'):
    setup_args['platforms'] = "win32 posix"


try:
    apply(setup, (), setup_args)
except distutils.errors.DistutilsPlatformError, ex:
    print
    print str(ex)

    print """
POSSIBLE CAUSE

"distutils" often needs developer support installed to work
correctly, which is usually located in a separate package 
called "python%d.%d-dev(el)".

Please contact the system administrator to have it installed.
""" % sys.version_info[:2]
    sys.exit(1)

