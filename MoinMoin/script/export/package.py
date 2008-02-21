# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Create a MoinMoin package from wiki pages specified.

    You must run this script as owner of the wiki files, usually this is the
    web server user.

    @copyright: 2002-2004 Juergen Hermann <jh@web.de>,
                2005-2006 MoinMoin:ThomasWaldmann,
                2007 Federico Lorenzi
    @license: GNU GPL, see COPYING for details.

"""

import codecs, errno, os, re, shutil, sys, time

from MoinMoin import config, wikiutil, Page, user
from MoinMoin import script


class PluginScript(script.MoinScript):
    """ Create package class """

    def __init__(self, argv=None, def_values=None):
        script.MoinScript.__init__(self, argv, def_values)
        self.parser.add_option(
            "-p", "--pages", dest="pages",
            help="List of pages to package. Can be regular expressions, comma seperated lists, or a lone * for everything."
        )
        self.parser.add_option(
            "-o", "--output", dest="output",
            help="Output file for the package."
        )
        self.parser.add_option(
            "-s", "--search", dest="search",
            help="Search string to match."
        )
        
        self.parser.add_option(
            "-u", "--user", dest="package_user",
            help="User as whom the package operation will be performed as. "
            )

    def mainloop(self):
        """ moin-package's main code. """
        
        # Initalize request
        self.init_request()
        request = self.request
        _ = self.request.getText
        
        # Check our command line args
        if self.options.pages and self.options.search:
            script.fatal(_("Options --pages and --search are mutually exclusive!"))
        elif not self.options.output:
            script.fatal(_("You must specify an output file!"))
        elif not self.options.pages and not self.options.search:
            script.log(_("No pages specified using --pages or --search, assuming full package."))

        # Sanity checks
        if os.path.exists(self.options.output):
            script.fatal(_("Output file already exists! Cowardly refusing to continue!"))
        
        # Check for user
        if self.options.package_user:
            request.user = user.User(request, name=self.options.package_user)
        
        # Import PackagePages here, as we now have an initalized request.
        from MoinMoin.action.PackagePages import PackagePages
        
        # Perform actual packaging.
        package = PackagePages(request.rootpage.page_name, request)
        packageoutput = open(self.options.output, "wb")
        if self.options.search:
            packagedata = package.collectpackage(package.searchpackage(request,
                                                                       self.options.search), packageoutput)
        elif self.options.pages:
                packagedata = package.collectpackage(self.options.pages.split(","), packageoutput)
        else:
                packagedata = package.collectpackage(request.rootpage.getPageList(
                                include_underlay=False, 
                                filter=lambda name: not wikiutil.isSystemPage(request, name)), 
                                packageoutput)
        if packagedata:
            script.fatal(packagedata)
