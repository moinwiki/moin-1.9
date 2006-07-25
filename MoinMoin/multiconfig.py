""" This is just a dummy file to overwrite MoinMoin/multiconfig.py(c) from a
    previous moin installation.

    The file moved to MoinMoin/config/multiconfig.py and you have to fix your
    imports as shown below.

    Alternatively, you can temporarily set show_configuration_error = False,
    so some compatibility code will get activated.
    But this compatibility code will get removed soon, so you really should
    update your config as soon as possible.
"""
show_configuration_error = True

if show_configuration_error:
    from MoinMoin.error import ConfigurationError
    raise ConfigurationError("""\
Please edit your wikiconfig/farmconfig and fix your DefaultConfig import:\r\n
\r\n
Old:   from MoinMoin.multiconfig import DefaultConfig\r\n
New:   from MoinMoin.config.multiconfig import DefaultConfig\r\n
\r\n
If you can't do that, but if you can change the MoinMoin code, see the file
MoinMoin/multiconfig.py for an alternative, but temporary workaround.
""")

else:
    from MoinMoin.config.multiconfig import *

