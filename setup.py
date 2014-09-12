#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
    MoinMoin installer

    @copyright: 2001-2005 by Jürgen Hermann <jh@web.de>,
                2006-2014 by MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import os, sys, glob

import distutils
from distutils.core import setup
from distutils.command.build_scripts import build_scripts

from MoinMoin.version import release, revision


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

def make_filelist(dir, strip_prefix=''):
    """ package_data is pretty stupid: if the globs that can be given there
        match a directory, then setup.py install will fall over that later,
        because it expects only files.
        Use make_filelist(dir, strip) to create a list of all FILES below dir,
        stripping off the strip_prefix at the left side.
    """
    found = []
    def _visit((found, strip), dirname, names):
        files = []
        for name in names:
            path = os.path.join(dirname, name)
            if os.path.isfile(path):
                if path.startswith(strip):
                    path = path[len(strip):]
                files.append(path)
        found.extend(files)

    os.path.walk(dir, _visit, (found, strip_prefix))
    return found

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
            module = module.replace('-', '_').replace('/', '.')
            script_vars = {
                'python': os.path.normpath(sys.executable),
                'package': self.package_name,
                'module': module,
                'package_location': '/usr/lib/python/site-packages', # FIXME: we need to know the correct path
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
    script = script.replace('_', '-')
    if sys.platform == "win32":
        script = script + ".bat"
    return script

# build list of scripts from their implementation modules
moin_scripts = [scriptname(fn) for fn in glob.glob('MoinMoin/script/[!_]*.py')]


#############################################################################
### Call setup()
#############################################################################

setup_args = {
    'name': "moin",
    'version': release,
    'description': "MoinMoin %s is an easy to use, full-featured and extensible wiki software package" % (release, ),
    'author': "Juergen Hermann et al.",
    'author_email': "moin-user@lists.sourceforge.net",
    # maintainer(_email) not active because distutils/register can't handle author and maintainer at once
    'download_url': 'http://static.moinmo.in/files/moin-%s.tar.gz' % (release, ),
    'url': "http://moinmo.in/",
    'license': "GNU GPL",
    'long_description': """
    MoinMoin is an easy to use, full-featured and extensible wiki software
    package written in Python. It can fulfill a wide range of roles, such as
    a personal notes organizer deployed on a laptop or home web server,
    a company knowledge base deployed on an intranet, or an Internet server
    open to individuals sharing the same interests, goals or projects.""",
    'classifiers': """Development Status :: 5 - Production/Stable
Environment :: No Input/Output (Daemon)
Environment :: Web Environment
Intended Audience :: Developers
Intended Audience :: System Administrators
Intended Audience :: Education
Intended Audience :: Science/Research
Intended Audience :: End Users/Desktop
Intended Audience :: Information Technology
License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)
Operating System :: OS Independent
Operating System :: POSIX
Operating System :: POSIX :: BSD
Operating System :: POSIX :: Linux
Operating System :: Unix
Operating System :: MacOS :: MacOS X
Operating System :: Microsoft :: Windows
Programming Language :: Python
Programming Language :: Python :: 2
Programming Language :: Python :: 2.5
Programming Language :: Python :: 2.6
Programming Language :: Python :: 2.7
Topic :: Internet :: WWW/HTTP :: Dynamic Content
Topic :: Internet :: WWW/HTTP :: WSGI
Topic :: Internet :: WWW/HTTP :: WSGI :: Application
Topic :: Office/Business :: Groupware
Topic :: Text Processing :: Markup""".splitlines(),

    'packages': [
        'jabberbot',
        'MoinMoin',
        'MoinMoin.action',
        'MoinMoin.auth',
        'MoinMoin.auth.openidrp_ext',
        'MoinMoin.config',
        'MoinMoin.converter',
        'MoinMoin.datastruct',
        'MoinMoin.datastruct.backends',
        'MoinMoin.events',
        'MoinMoin.filter',
        'MoinMoin.formatter',
        'MoinMoin.i18n',
        'MoinMoin.i18n.tools',
        'MoinMoin.logfile',
        'MoinMoin.macro',
        'MoinMoin.mail',
        'MoinMoin.parser',
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
        'MoinMoin.script.server',
        'MoinMoin.script.xmlrpc',
        'MoinMoin.search',
        'MoinMoin.search.Xapian',
        'MoinMoin.search.queryparser',
        'MoinMoin.security',
        'MoinMoin.stats',
        'MoinMoin.support',
        'MoinMoin.support.flup',
        'MoinMoin.support.flup.client',
        'MoinMoin.support.flup.server',
        'MoinMoin.support.passlib',
        'MoinMoin.support.passlib._setup',
        'MoinMoin.support.passlib.ext',
        'MoinMoin.support.passlib.ext.django',
        'MoinMoin.support.passlib.handlers',
        'MoinMoin.support.passlib.utils',
        'MoinMoin.support.passlib.utils._blowfish',
        'MoinMoin.support.pygments',
        'MoinMoin.support.pygments.filters',
        'MoinMoin.support.pygments.formatters',
        'MoinMoin.support.pygments.lexers',
        'MoinMoin.support.pygments.styles',
        'MoinMoin.support.werkzeug',
        'MoinMoin.support.werkzeug.contrib',
        'MoinMoin.support.werkzeug.debug',
        'MoinMoin.support.xappy',
        'MoinMoin.support.parsedatetime',
        'MoinMoin.theme',
        'MoinMoin.userform',
        'MoinMoin.userprefs',
        'MoinMoin.util',
        'MoinMoin.web',
        'MoinMoin.web.static',
        'MoinMoin.widget',
        'MoinMoin.wikixml',
        'MoinMoin.xmlrpc',

        # all other _tests are missing here, either we have all or nothing:
        #'MoinMoin._tests',
    ],

    'package_dir': {'MoinMoin.i18n': 'MoinMoin/i18n',
                    'MoinMoin.web.static': 'MoinMoin/web/static',
                   },
    'package_data': {'MoinMoin.i18n': ['README', 'Makefile', 'MoinMoin.pot', 'POTFILES.in',
                                       '*.po',
                                       'tools/*',
                                       'jabberbot/*',
                                      ],
                     'MoinMoin.web.static': make_filelist('MoinMoin/web/static/htdocs',
                                                          strip_prefix='MoinMoin/web/static/'),
                    },

    # Override certain command classes with our own ones
    'cmdclass': {
        'build_scripts': build_scripts_moin,
    },

    'scripts': moin_scripts,

    # This copies the contents of wiki dir under sys.prefix/share/moin
    # Do not put files that should not be installed in the wiki dir, or
    # clean the dir before you make the distribution tarball.
    'data_files': makeDataFiles('share/moin', 'wiki')
}

if hasattr(distutils.dist.DistributionMetadata, 'get_keywords'):
    setup_args['keywords'] = "wiki web"

if hasattr(distutils.dist.DistributionMetadata, 'get_platforms'):
    setup_args['platforms'] = "any"


if __name__ == '__main__':
    try:
        setup(**setup_args)
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

