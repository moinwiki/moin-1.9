# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - image/jpeg Filter

    @copyright: 2006 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""
import EXIF

def execute(indexobj, filename):
    """ Extract some EXIF data """
    try:
        f = file(filename, 'rb')
        tags = EXIF.process_file(f)
        f.close()
        # get rid of some big stuff:
        try:
            del tags["JPEGThumbnail"]
        except:
            pass
        try:
            del tags["EXIF MakerNote"]
        except:
            pass
        data = str(tags).decode('utf-8')
    except (ValueError, TypeError): # EXIF throws ValueError on unknown tags
                                    #             TypeError on other occassions
        data = u''
    return data

