# -*- coding: utf-8 -*-
"""
    MoinMoin - MoinMoin.mail.mailimport Tests

    @copyright: 2020 Thomas Waldmann <tw@waldmann-edv.de>
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.mail import mailimport


class TestMailHeaderParsing:
    _tests = (
        # simple email address (localhost)
        (['From: user', ],
         [(u'', u'user'), ]),

        # only fully-qualified email address, no realname part
        (['From: user@example.org', ],
         [(u'', u'user@example.org'), ]),

        # simple realname part without quotes:
        (['From: Joe Doe <user@example.org>', ],
         [(u'Joe Doe', u'user@example.org'), ]),

        # realname part with comma, must be quoted:
        (['From: "Doe, Joe" <user@example.org>', ],
         [(u'Doe, Joe', u'user@example.org'), ]),

        # realname part is RFC2044-encoded but pure ascii:
        # no comma
        (['From: =?utf-8?q?Joe_Doe?= <user@example.org>', ],
         [(u'Joe Doe', u'user@example.org'), ]),
        # realname part containing a comma
        (['From: =?utf-8?q?Doe=2C_Joe?= <user@example.org>', ],
         [(u'Doe, Joe', u'user@example.org'), ]),

        # realname part has RFC2044-encoded non-ascii chars:
        # no comma
        (['From: =?utf-8?b?SsO2IETDtg==?= <user@example.org>', ],
         [(u'Jö Dö', u'user@example.org'), ]),
        # realname part containing a comma
        (['From: =?utf-8?b?RMO2LCBKw7Y=?= <user@example.org>', ],
         [(u'Dö, Jö', u'user@example.org'), ]),
    )

    def test_parsing(self):
        for input, expected in self._tests:
            assert mailimport._get_addrs(input) == expected


coverage_modules = ['MoinMoin.mail.mailimport']
