#!/usr/bin/python
"""
    convert some markup contained in po files to new link/macro markup
"""
DOMAIN = "MoinMoin"

import re
import sys
import codecs

def run():
    sys.path.insert(0, '../..')

    lang = sys.argv[1]

    f = codecs.open("%s.%s.po" % (lang, DOMAIN), "r", "utf-8")
    text = f.read()
    f.close()

    # replace [[Macro(...)]] by <<Macro(...)>>
    macro_rule = r"\[\[(?P<macro>.*?)\]\]"
    macro_repl = r"<<\g<macro>>>"
    macro_re = re.compile(macro_rule, re.U|re.M|re.S)
    text = macro_re.sub(macro_repl, text)

    #print repr(text)

    f = codecs.open("%s.%s.po" % (lang, DOMAIN), "w", "utf-8")
    f.write(text)
    f.close()

if __name__ == "__main__":
    run()

