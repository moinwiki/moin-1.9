# -*- coding: iso-8859-1 -*-
"""
    Outputs the text verbatimly.

    @copyright: 2005 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details
"""

Dependencies = []

def execute(macro, args):
    return macro.formatter.escapedText(args)
