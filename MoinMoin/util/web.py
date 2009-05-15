# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Helper functions for WWW stuff

    @copyright: 2002 Juergen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

def getIntegerInput(request, fieldname, default=None, minval=None, maxval=None):
    """ Get an integer value from a request parameter. If the value
        is out of bounds, it's made to fit into those bounds.

        Returns `default` in case of errors (not a valid integer, or field
        is missing).
    """
    try:
        result = int(request.values[fieldname])
    except (KeyError, ValueError):
        return default
    else:
        if minval is not None:
            result = max(result, minval)
        if maxval is not None:
            result = min(result, maxval)
        return result


def makeSelection(name, values, selectedval=None, size=1, multiple=False, enabled=True):
    """ Make a HTML <select> element named `name` from a value list.
        The list can either be a list of strings, or a list of
        (value, label) tuples.

        `selectedval` is the value that should be pre-selected.
    """
    from MoinMoin.widget import html
    result = html.SELECT(name=name, size="%d" % int(size), multiple=multiple, disabled=not enabled)
    for val in values:
        if not isinstance(val, type(())):
            val = (val, val)
        result.append(html.OPTION(
            value=val[0], selected=(val[0] == selectedval))
            .append(html.Text(val[1]))
        )

    return result

def makeMultiSelection(name, values, selectedvals=None, size=5, enabled=True):
    """Make a HTML multiple <select> element with named `name` from a value list.

    The list can either be a list of strings, or a list of (value, label) tuples.
    `selectedvals` is a list of values that should be pre-selected.

    """
    from MoinMoin.widget import html
    result = html.SELECT(name=name, size="%d" % int(size), multiple=True, disabled=not enabled)
    for val in values:
        if not isinstance(val, type(())):
            val = (val, val)
        result.append(html.OPTION(
            value=val[0], selected=(val[0] in selectedvals))
            .append(html.Text(val[1]))
        )

    return result

class Color:
    """ RGB-Triple that automatically converts from and to
        "#RRGGBB" encoding, and also takes Netscape color names.

        The color values are stored in the attributes `r`, `g` and `b`.

        Example:
            >>> from color import Color
            >>> Color('yellow')
            Color(255, 255, 0)
            >>> str(Color('yellow'))
            '#FFFF00'
            >>> str(Color((128, 0, 128)))
            '#800080'
            >>> Color('#FF00FF')
            Color(255, 0, 255)
    """

    COLORS = {
        'aliceblue': (0xF0, 0xF8, 0xFF),
        'antiquewhite': (0xFA, 0xEB, 0xD7),
        'aqua': (0x00, 0xFF, 0xFF),
        'aquamarine': (0x7F, 0xFF, 0xD4),
        'azure': (0xF0, 0xFF, 0xFF),
        'beige': (0xF5, 0xF5, 0xDC),
        'bisque': (0xFF, 0xE4, 0xC4),
        'black': (0x00, 0x00, 0x00),
        'blanchedalmond': (0xFF, 0xEB, 0xCD),
        'blue': (0x00, 0x00, 0xFF),
        'blueviolet': (0x8A, 0x2B, 0xE2),
        'brown': (0xA5, 0x2A, 0x2A),
        'burlywood': (0xDE, 0xB8, 0x87),
        'cadetblue': (0x5F, 0x9E, 0xA0),
        'chartreuse': (0x7F, 0xFF, 0x00),
        'chocolate': (0xD2, 0x69, 0x1E),
        'coral': (0xFF, 0x7F, 0x50),
        'cornflowerblue': (0x64, 0x95, 0xED),
        'cornsilk': (0xFF, 0xF8, 0xDC),
        'crimson': (0xDC, 0x14, 0x3C),
        'cyan': (0x00, 0xFF, 0xFF),
        'darkblue': (0x00, 0x00, 0x8B),
        'darkcyan': (0x00, 0x8B, 0x8B),
        'darkgoldenrod': (0xB8, 0x86, 0x0B),
        'darkgray': (0xA9, 0xA9, 0xA9),
        'darkgreen': (0x00, 0x64, 0x00),
        'darkkhaki': (0xBD, 0xB7, 0x6B),
        'darkmagenta': (0x8B, 0x00, 0x8B),
        'darkolivegreen': (0x55, 0x6B, 0x2F),
        'darkorange': (0xFF, 0x8C, 0x00),
        'darkorchid': (0x99, 0x32, 0xCC),
        'darkred': (0x8B, 0x00, 0x00),
        'darksalmon': (0xE9, 0x96, 0x7A),
        'darkseagreen': (0x8F, 0xBC, 0x8F),
        'darkslateblue': (0x48, 0x3D, 0x8B),
        'darkslategray': (0x2F, 0x4F, 0x4F),
        'darkturquoise': (0x00, 0xCE, 0xD1),
        'darkviolet': (0x94, 0x00, 0xD3),
        'deeppink': (0xFF, 0x14, 0x93),
        'deepskyblue': (0x00, 0xBF, 0xFF),
        'dimgray': (0x69, 0x69, 0x69),
        'dodgerblue': (0x1E, 0x90, 0xFF),
        'firebrick': (0xB2, 0x22, 0x22),
        'floralwhite': (0xFF, 0xFA, 0xF0),
        'forestgreen': (0x22, 0x8B, 0x22),
        'fuchsia': (0xFF, 0x00, 0xFF),
        'gainsboro': (0xDC, 0xDC, 0xDC),
        'ghostwhite': (0xF8, 0xF8, 0xFF),
        'gold': (0xFF, 0xD7, 0x00),
        'goldenrod': (0xDA, 0xA5, 0x20),
        'gray': (0x80, 0x80, 0x80),
        'green': (0x00, 0x80, 0x00),
        'greenyellow': (0xAD, 0xFF, 0x2F),
        'honeydew': (0xF0, 0xFF, 0xF0),
        'hotpink': (0xFF, 0x69, 0xB4),
        'indianred': (0xCD, 0x5C, 0x5C),
        'indigo': (0x4B, 0x00, 0x82),
        'ivory': (0xFF, 0xFF, 0xF0),
        'khaki': (0xF0, 0xE6, 0x8C),
        'lavender': (0xE6, 0xE6, 0xFA),
        'lavenderblush': (0xFF, 0xF0, 0xF5),
        'lawngreen': (0x7C, 0xFC, 0x00),
        'lemonchiffon': (0xFF, 0xFA, 0xCD),
        'lightblue': (0xAD, 0xD8, 0xE6),
        'lightcoral': (0xF0, 0x80, 0x80),
        'lightcyan': (0xE0, 0xFF, 0xFF),
        'lightgoldenrodyellow': (0xFA, 0xFA, 0xD2),
        'lightgreen': (0x90, 0xEE, 0x90),
        'lightgrey': (0xD3, 0xD3, 0xD3),
        'lightpink': (0xFF, 0xB6, 0xC1),
        'lightsalmon': (0xFF, 0xA0, 0x7A),
        'lightseagreen': (0x20, 0xB2, 0xAA),
        'lightskyblue': (0x87, 0xCE, 0xFA),
        'lightslategray': (0x77, 0x88, 0x99),
        'lightsteelblue': (0xB0, 0xC4, 0xDE),
        'lightyellow': (0xFF, 0xFF, 0xE0),
        'lime': (0x00, 0xFF, 0x00),
        'limegreen': (0x32, 0xCD, 0x32),
        'linen': (0xFA, 0xF0, 0xE6),
        'magenta': (0xFF, 0x00, 0xFF),
        'maroon': (0x80, 0x00, 0x00),
        'mediumaquamarine': (0x66, 0xCD, 0xAA),
        'mediumblue': (0x00, 0x00, 0xCD),
        'mediumorchid': (0xBA, 0x55, 0xD3),
        'mediumpurple': (0x93, 0x70, 0xDB),
        'mediumseagreen': (0x3C, 0xB3, 0x71),
        'mediumslateblue': (0x7B, 0x68, 0xEE),
        'mediumspringgreen': (0x00, 0xFA, 0x9A),
        'mediumturquoise': (0x48, 0xD1, 0xCC),
        'mediumvioletred': (0xC7, 0x15, 0x85),
        'midnightblue': (0x19, 0x19, 0x70),
        'mintcream': (0xF5, 0xFF, 0xFA),
        'mistyrose': (0xFF, 0xE4, 0xE1),
        'moccasin': (0xFF, 0xE4, 0xB5),
        'navajowhite': (0xFF, 0xDE, 0xAD),
        'navy': (0x00, 0x00, 0x80),
        'oldlace': (0xFD, 0xF5, 0xE6),
        'olive': (0x80, 0x80, 0x00),
        'olivedrab': (0x6B, 0x8E, 0x23),
        'orange': (0xFF, 0xA5, 0x00),
        'orangered': (0xFF, 0x45, 0x00),
        'orchid': (0xDA, 0x70, 0xD6),
        'palegoldenrod': (0xEE, 0xE8, 0xAA),
        'palegreen': (0x98, 0xFB, 0x98),
        'paleturquoise': (0xAF, 0xEE, 0xEE),
        'palevioletred': (0xDB, 0x70, 0x93),
        'papayawhip': (0xFF, 0xEF, 0xD5),
        'peachpuff': (0xFF, 0xDA, 0xB9),
        'peru': (0xCD, 0x85, 0x3F),
        'pink': (0xFF, 0xC0, 0xCB),
        'plum': (0xDD, 0xA0, 0xDD),
        'powderblue': (0xB0, 0xE0, 0xE6),
        'purple': (0x80, 0x00, 0x80),
        'red': (0xFF, 0x00, 0x00),
        'rosybrown': (0xBC, 0x8F, 0x8F),
        'royalblue': (0x41, 0x69, 0xE1),
        'saddlebrown': (0x8B, 0x45, 0x13),
        'salmon': (0xFA, 0x80, 0x72),
        'sandybrown': (0xF4, 0xA4, 0x60),
        'seagreen': (0x2E, 0x8B, 0x57),
        'seashell': (0xFF, 0xF5, 0xEE),
        'sienna': (0xA0, 0x52, 0x2D),
        'silver': (0xC0, 0xC0, 0xC0),
        'skyblue': (0x87, 0xCE, 0xEB),
        'slateblue': (0x6A, 0x5A, 0xCD),
        'slategray': (0x70, 0x80, 0x90),
        'snow': (0xFF, 0xFA, 0xFA),
        'springgreen': (0x00, 0xFF, 0x7F),
        'steelblue': (0x46, 0x82, 0xB4),
        'tan': (0xD2, 0xB4, 0x8C),
        'teal': (0x00, 0x80, 0x80),
        'thistle': (0xD8, 0xBF, 0xD8),
        'tomato': (0xFF, 0x63, 0x47),
        'turquoise': (0x40, 0xE0, 0xD0),
        'violet': (0xEE, 0x82, 0xEE),
        'wheat': (0xF5, 0xDE, 0xB3),
        'white': (0xFF, 0xFF, 0xFF),
        'whitesmoke': (0xF5, 0xF5, 0xF5),
        'yellow': (0xFF, 0xFF, 0x00),
        'yellowgreen': (0x9A, 0xCD, 0x32),
    }

    def __init__(self, color):
        """ Init color value, the 'color' parameter may be
            another Color instance, a tuple containing 3 color values,
            a Netscape color name or a HTML color ("#RRGGBB").
        """
        if isinstance(color, tuple) and len(color) == 3:
            self.r, self.g, self.b = int(color[0]), int(color[1]), int(color[2])
        elif isinstance(color, Color):
            self.r, self.g, self.b = color.r, color.g, color.b
        elif not isinstance(color, str):
            raise TypeError("Color() expects a Color instance, a RGB triple or a color string")
        elif color[0] == '#':
            color = long(color[1:], 16)
            self.r = (color >> 16) & 255
            self.g = (color >> 8) & 255
            self.b = color & 255
        elif color not in self.COLORS:
            raise ValueError("Unknown color name '%s'" % color)
        else:
            # known color name
            self.r, self.g, self.b = self.COLORS[color]

    def __str__(self):
        return "#%02X%02X%02X" % (self.r, self.g, self.b)

    def __repr__(self):
        return "Color(%d, %d, %d)" % (self.r, self.g, self.b)

    def __int__(self):
        return self.__long__()

    def __long__(self):
        return (self.r << 16) | (self.g << 8) | self.b

