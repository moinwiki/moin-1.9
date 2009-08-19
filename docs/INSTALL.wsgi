MoinMoin - setting up the WSGI application
==========================================

This manual describes how to setup a MoinMoin instance to run under
various webservers and gateway interfaces. We assume, that you already
followed through the basic installation and set up a wiki instance,
either system wide or as a user:

 * http://moinmo.in/HelpOnInstalling/BasicInstallation
 * http://moinmo.in/HelpOnInstalling/WikiInstanceCreation

In the following the install prefix of where you installed MoinMoin will
be called $PREFIX, and your wiki instance will be called $INSTANCE.

= Running the application =

There are several ways to run MoinMoin, with varying complexity and
performance. The most common ways are:

 * CGI: the classic among web application serving, awfully slow but
    works (almost) everywhere.
 * FastCGI (and other modern gateway interfaces): very fast, leaves
    static fileserving and HTTP protocol to the webserver
 * Standalone server: reasonably fast, but static file serving can be
    improved with a standard webserver in front.
 * mod_wsgi: Apache can embed a python process into the webserver, that
    speaks directly with the MoinMoin WSGI application. Very fast and
    for the future the preferred method of deployment.

== Running as CGI ==
Almost every webserver supports running CGI scripts. To serve MoinMoin
wiki pages, the `moin.cgi` script needs to be made accessable and
executable by the server. Usually the webserver runs not as user `root`,
but as some other user and group for security reasons. in the following
the user the webserver runs as will be called $USER and the group will
be called $GROUP.

  > cd $INSTANCE
  > mkdir cgi-bin
  > cp $PREFIX/share/moin/server/moin.cgi cgi-bin/
  > chown -R $USER:$GROUP cgi-bin
  > chmod -R ug+rx cgi-bin
  > chmod -R o-rwx cgi-bin

In this scenario we create the directory `cgi-bin` directly in the
instance directory of the wiki. If you already have another designated
directory for CGI files, you may just copy `moin.cgi` there. Since the
paths for your particular wiki instance are configurable, the location
does not really matter in relation to where your instance directory is.

=== Configure the webserver ===
To make Apache run your wiki instance correctly, it still needs to know
about your CGI script and the location of the static files of MoinMoin
(like images, stylesheets, etc.). Also it should not make the instance
directory accessable over the web. Add the following to your Apache
configuration, either global or inside the desired virtual host.

  Alias /moin_static180 $PREFIX/share/moin/htdocs/
  ScriptAlias /wiki $INSTANCE/cgi-bin/moin.cgi

If you plan an running several instances on the server, either in
different vhosts or under different URLs, you may add the `Alias`-line
to the global server config once and omit it for the different instances
altogether.

If you placed `moin.cgi` in a different, already configured directory,
as mentioned above, just omit the `ScriptAlias`-line.

=== Configure moin.cgi ===
When `moin.cgi` is launched, the python interpreter imports the modules
needed to run MoinMoin and those in turn import the wiki configuration
(which is itself a python module). While the MoinMoin modules should
always be found in a properly configured system (as described in
http://moinmo.in/HelpOnInstalling/BasicInstallation), it is likely that
the configuration file will not be found. Edit the `moin.cgi` script to
correct that. You will find a section labelled `a2)`, which is
commented out. Change it, so that it points to your instance directory.

sys.path.insert(0, '$INSTANCE')

/!\ Attention here, the comment mark `#` has to be removed. /!\

=== Check wikiconfig.py again ===
Finally, check that the `wikiconfig.py` file in the instance directory
contains correct paths for:

 * `url_prefix_static` (static stuff like css/img/js)
 * `data_dir` (the instance data directory) and
 * `data_underlay_dir` (the instance underlay directory).

/!\ You could use relative paths for those directories (relative to the
location of `moin.cgi`), but to save yourself some headaches just use
absolute paths.

When following this guide the paths look like this:

    data_dir = '$INSTANCE/data/'
    data_underlay_dir = '$INSTANCE/underlay/'
    url_prefix_static = '/moin_static180' # depends on moin version

There are other settings you will likely want to alter, look at the
bottom of http://moinmo.in/HelpOnInstalling/WikiInstanceCreation for
more details about them.

== Running as FastCGI (or similar) ==
[...] # TODO: write this

== Running as Standalone server ==
[...] # TODO: write this

== Running with mod_wsgi ==
[...] # TODO: write this

== Test the wiki ==
Everything should work fine now. It is time to restart the Apache server
(usually with `/etc/init.d/apache restart`, sometimes with
`apachectl restart`) and perform the following steps:

 * Access your new wiki with the URL `http://127.0.0.1/wiki/` (or the
   name and port you have defined in the Apache configuration file). You
   should see some wiki page - read it.
 * Then go to the WikiSandBox page.
 * Try to edit it and save your changes.
 * If that works, see if your edit is shown on the RecentChanges page.
 * If you see them, congratulations, your new wiki works! :)

/!\ In case something goes wrong, have a look at the generic
troubleshooting guide at:

http://moinmo.in/HelpOnInstalling/TroubleShooting

A common problem is the inability of the webserver to access your CGI
script or static files. In case of the Apache webserver, you can check
and augment your Apache config file for the following directives:

  <Directory "$PREFIX/moin/htdocs/">
     Order deny,allow
     Allow from all
  </Directory>

  <Directory "$INSTANCE/cgi-bin">
     Order deny,allow
     Allow from all
  </Directory>
