"""
    MoinMoin - Support Package

    Stuff for compatibility with older Python versions

    @copyright: 2007 Heinrich Wendel <heinrich.wendel@gmail.com>,
                2007 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

"""
This is a feature from python 2.4, needed for compatibility with python 2.3,
although it may not be 100% compatible.
"""
try:
    import string
    rsplit = string.rsplit
except AttributeError:
    # CAUTION: you can't use s.rsplit(...), only rsplit(s, ...) with this!
    def rsplit(s, sep=None, maxsplit=-1):
        """rsplit(s [,sep [,maxsplit]]) -> list of strings

        Return a list of the words in the string s, using sep as the
        delimiter string, starting at the end of the string and working
        to the front.  If maxsplit is given, at most maxsplit splits are
        done. If sep is not specified or is None, any whitespace string
        is a separator.
        """
        fragments = s[::-1].split(sep, maxsplit)
        return [fragment[::-1] for fragment in fragments[::-1]]

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
    frozenset = frozenset
except NameError:
    from sets import Set as set
    from sets import ImmutableSet as frozenset

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

"""
This is a feature from python 2.5, needed for compatibility with python 2.3 and 2.4,
although it may not be 100% compatible.
"""
try:
    import hashlib, hmac
    hash_new = hashlib.new
    def hmac_new(key, msg, digestmod=hashlib.sha1):
        return hmac.new(key, msg, digestmod)

except (NameError, ImportError):
    import sha
    def hash_new(name, string=''):
        if name in ('SHA1', 'sha1'):
            return sha.new(string)
        elif name in ('MD5', 'md5'):
            import md5
            return md5.new(string)
        raise ValueError("unsupported hash type")

    def hmac_new(key, msg, digestmod=sha):
        import hmac
        return hmac.new(key, msg, digestmod)

