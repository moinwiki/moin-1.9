"""
    MoinMoin - Support Package

    Stuff for compatibility with older pytohn versions

    @copyright: 2007 Heinrich Wendel <heinrich.wendel@gmail.com>
    @license: GNU GPL, see COPYING for details.
"""

"""
This is a feature from python 2.4, needed for compatibility with python 2.3,
although it may not be 100% compatible.
"""
try:
    sorted = sorted
except NameError:
    def sorted(l, *args, **kw):
        if type(l) == dict:
            l = l.keys()
        l = l[:]
        # py2.3 is a bit different
        if 'cmp' in kw:
            args = (kw['cmp'], )

        l.sort(*args)
        return l

"""
This is a feature from python 2.4, needed for compatibility with python 2.3,
although it may not be 100% compatible.
"""
try:
    set = set
except NameError:
    from sets import Set as set

"""
This is a feature from python 2.5, needed for compatibility with python 2.3 and 2.4.
"""
try:
    from functools import partial
except (NameError, ImportError):
    class partial(object):
        def __init__(*args, **kw):
            self = args[0]
            self.fn, self.args, self.kw = (args[1], args[2:], kw)

        def __call__(self, *args, **kw):
            if kw and self.kw:
                d = self.kw.copy()
                d.update(kw)
            else:
                d = kw or self.kw
            return self.fn(*(self.args + args), **d)
