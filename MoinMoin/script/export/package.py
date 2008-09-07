# -*- coding: iso-8859-1 -*-
"""
MoinMoin - Create a MoinMoin package from wiki pages specified.

@copyright: 2002-2004 Juergen Hermann <jh@web.de>
            2005-2006 MoinMoin:ThomasWaldmann,
            2007 Federico Lorenzi
@license: GNU GPL, see COPYING for details.
"""

import os

from MoinMoin import wikiutil, user
from MoinMoin import script


class PluginScript(script.MoinScript):
    """\
Purpose:
========
This tool allows you to create a package of certain wiki pages.

Detailed Instructions:
======================
General syntax: moin [options] export package [package-options]

[options] usually should be:
    --config-dir=/path/to/my/cfg/ --wiki-url=wiki.example.org/

[package-options] see below:
    0. You must run this script as owner of the wiki files, usually this is the
       web server user.

    1. To package all non-system and non-underlay pages on a wiki to the file '~/mywiki.zip'
       moin ... export package --output ~/mywiki.zip

    2. To package the pages 'FooBar' and 'TestPage' on a wiki to the file '~/mywiki.zip'
       moin ... export package --pages FooBar,TestPage --output ~/mywiki.zip

    3. To package all pages matching the search term 'MoinMoin' on a wiki to the file '~/mywiki.zip'
       moin ... export package --search MoinMoin --output ~/mywiki.zip

    4. Optionally, the --user argument could be added to any of the above examples,
       causing the script to respect ACLs.

    5. Optionally, the --include_attachments argument could be added to any of the above examples,
       causing the script to include attachments into the output file.
"""

    def __init__(self, argv=None, def_values=None):
        script.MoinScript.__init__(self, argv, def_values)
        self.parser.add_option(
            "-p", "--pages", dest="pages",
            help="List of pages to package. Can be regular expressions, comma seperated lists, or a lone * for everything."
        )
        self.parser.add_option(
            "-a", "--include_attachments", action="store_true", dest="attachment",
            help="Include attachments from each page"
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

        include_attachments = self.options.attachment or False
        if include_attachments:
            script.log(_("All attachments included into the package."))

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
                                                                       self.options.search), packageoutput,
                                                                       include_attachments=include_attachments)
        elif self.options.pages:
            packagedata = package.collectpackage(self.options.pages.split(","), packageoutput, include_attachments=include_attachments)
        else:
            packagedata = package.collectpackage(request.rootpage.getPageList(
                                include_underlay=False,
                                filter=lambda name: not wikiutil.isSystemPage(request, name)),
                                packageoutput, include_attachments=include_attachments)
        if packagedata:
            script.fatal(packagedata)

