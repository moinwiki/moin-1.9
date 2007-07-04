# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Charts

    This is a wrapper for the "gdchart" module.

    Example:
        import random
        c = Chart()
        c.addData(ChartData([random.gauss(0, 5.0) for i in range(20)], color='blue'))
        c.option(title = 'gdchart Demo')
        c.draw(Chart.GDC_LINE, (600, 300), 'test.gif')

    @copyright: 2002-2004 Juergen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import gdchart
from MoinMoin.util.web import Color


class ChartData:
    """ Data set for one line in a chart, including
        properties like the color of that line.
    """
    def __init__(self, data, color='black'):
        """
        Create a data set.

        @param data: tuple / list of numbers
        @param color: rendering color (triple, '#RRGGBB' or color name)
        """
        self.data = data
        self.color = color


class Chart:
    """ Wrapper for "gdchart".

        All GDC* constants are available as class attributes.
    """

    DEFAULTS = gdchart.option()

    def __init__(self):
        # Get a copy of the default options
        self.options = self.DEFAULTS.copy()
        self.datasets = []

        self.option(
            bg_color=0xffffff,
            line_color=0x000000,
        )

    def addData(self, data):
        self.datasets.append(data)

    def option(self, **args):
        # Save option values in the object's dictionary.
        self.options.update(args)

    def draw(self, style, size, output, labels=None):
        args = []
        colors = []
        for dataset in self.datasets:
            if isinstance(dataset, ChartData):
                args.append(dataset.data)
                colors.append(dataset.color)
            else:
                args.append(dataset)
                colors.append('black')

        # Default for X axis labels (numbered 1..n)
        if not labels:
            labels = [str(i) for i in range(1, len(args[0])+1)]

        # set colors for the data sets
        if colors:
            self.option(set_color=[int(Color(c)) for c in colors])

        # pass options to gdchart and render the chart
        gdchart.option(**self.options)

        # limit label length in order to workaround bugs in gdchart
        labels = [x[:32] for x in labels]
        gdchart.chart(*((style, size, output, labels) + tuple(args)))


# copy GDC constants to Chart's namespace
for key, val in vars(gdchart).items():
    if key.startswith('GDC'):
        setattr(Chart, key, val)


if __name__ == "__main__":
    import os, sys, random
    c = Chart()
    c.addData(ChartData([random.randrange(0, i+1) for i in range(20)], color='green'))
    c.addData(ChartData([random.gauss(30, 5.0) for i in range(20)], color='blue'))
    c.option(
        title='gdchart Demo',
        xtitle='X axis',
        ytitle='random values',
    )
    c.draw(Chart.GDC_LINE, (600, 300), 'test.gif')
    if sys.platform == "win32":
        os.system("explorer test.gif")
    else:
        os.system("display test.gif &")

