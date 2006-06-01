# Library to extract EXIF information in digital camera image files
#
# To use this library call with:
#    f=open(path_name, 'rb')
#    tags=EXIF.process_file(f)
# tags will now be a dictionary mapping names of EXIF tags to their
# values in the file named by path_name.  You can process the tags
# as you wish.  In particular, you can iterate through all the tags with:
#     for tag in tags.keys():
#         if tag not in ('JPEGThumbnail', 'TIFFThumbnail', 'Filename',
#                        'EXIF MakerNote'):
#             print "Key: %s, value %s" % (tag, tags[tag])
# (This code uses the if statement to avoid printing out a few of the
# tags that tend to be long or boring.)
#
# The tags dictionary will include keys for all of the usual EXIF
# tags, and will also include keys for Makernotes used by some
# cameras, for which we have a good specification.
#
# Contains code from "exifdump.py" originally written by Thierry Bousch
# <bousch@topo.math.u-psud.fr> and released into the public domain.
#
# Updated and turned into general-purpose library by Gene Cash
#
# This copyright license is intended to be similar to the FreeBSD license.
#
# Copyright 2002 Gene Cash All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#    1. Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#    2. Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the
#       distribution.
#
# THIS SOFTWARE IS PROVIDED BY GENE CASH ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
# OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# This means you may do anything you want with this code, except claim you
# wrote it. Also, if it breaks you get to keep both pieces.
#
# Patch Contributors:
# * Simon J. Gerraty <sjg@crufty.net>
#   s2n fix & orientation decode
# * John T. Riedl <riedl@cs.umn.edu>
#   Added support for newer Nikon type 3 Makernote format for D70 and some
#   other Nikon cameras.
# * Joerg Schaefer <schaeferj@gmx.net>
#   Fixed subtle bug when faking an EXIF header, which affected maker notes
#   using relative offsets, and a fix for Nikon D100.
#
# 21-AUG-99 TB  Last update by Thierry Bousch to his code.
# 17-JAN-02 CEC Discovered code on web.
#               Commented everything.
#               Made small code improvements.
#               Reformatted for readability.
# 19-JAN-02 CEC Added ability to read TIFFs and JFIF-format JPEGs.
#               Added ability to extract JPEG formatted thumbnail.
#               Added ability to read GPS IFD (not tested).
#               Converted IFD data structure to dictionaries indexed by
#               tag name.
#               Factored into library returning dictionary of IFDs plus
#               thumbnail, if any.
# 20-JAN-02 CEC Added MakerNote processing logic.
#               Added Olympus MakerNote.
#               Converted data structure to single-level dictionary, avoiding
#               tag name collisions by prefixing with IFD name.  This makes
#               it much easier to use.
# 23-JAN-02 CEC Trimmed nulls from end of string values.
# 25-JAN-02 CEC Discovered JPEG thumbnail in Olympus TIFF MakerNote.
# 26-JAN-02 CEC Added ability to extract TIFF thumbnails.
#               Added Nikon, Fujifilm, Casio MakerNotes.
# 30-NOV-03 CEC Fixed problem with canon_decode_tag() not creating an
#               IFD_Tag() object.
# 15-FEB-04 CEC Finally fixed bit shift warning by converting Y to 0L.
#

# field type descriptions as (length, abbreviation, full name) tuples
FIELD_TYPES=(
    (0, 'X',  'Proprietary'), # no such type
    (1, 'B',  'Byte'),
    (1, 'A',  'ASCII'),
    (2, 'S',  'Short'),
    (4, 'L',  'Long'),
    (8, 'R',  'Ratio'),
    (1, 'SB', 'Signed Byte'),
    (1, 'U',  'Undefined'),
    (2, 'SS', 'Signed Short'),
    (4, 'SL', 'Signed Long'),
    (8, 'SR', 'Signed Ratio')
    )

# dictionary of main EXIF tag names
# first element of tuple is tag name, optional second element is
# another dictionary giving names to values
EXIF_TAGS={
    0x0100: ('ImageWidth', ),
    0x0101: ('ImageLength', ),
    0x0102: ('BitsPerSample', ),
    0x0103: ('Compression',
             {1: 'Uncompressed TIFF',
              6: 'JPEG Compressed'}),
    0x0106: ('PhotometricInterpretation', ),
    0x010A: ('FillOrder', ),
    0x010D: ('DocumentName', ),
    0x010E: ('ImageDescription', ),
    0x010F: ('Make', ),
    0x0110: ('Model', ),
    0x0111: ('StripOffsets', ),
    0x0112: ('Orientation',
             {1: 'Horizontal (normal)',
              2: 'Mirrored horizontal',
              3: 'Rotated 180',
              4: 'Mirrored vertical',
              5: 'Mirrored horizontal then rotated 90 CCW',
              6: 'Rotated 90 CW',
              7: 'Mirrored horizontal then rotated 90 CW',
              8: 'Rotated 90 CCW'}),
    0x0115: ('SamplesPerPixel', ),
    0x0116: ('RowsPerStrip', ),
    0x0117: ('StripByteCounts', ),
    0x011A: ('XResolution', ),
    0x011B: ('YResolution', ),
    0x011C: ('PlanarConfiguration', ),
    0x0128: ('ResolutionUnit',
             {1: 'Not Absolute',
              2: 'Pixels/Inch',
              3: 'Pixels/Centimeter'}),
    0x012D: ('TransferFunction', ),
    0x0131: ('Software', ),
    0x0132: ('DateTime', ),
    0x013B: ('Artist', ),
    0x013E: ('WhitePoint', ),
    0x013F: ('PrimaryChromaticities', ),
    0x0156: ('TransferRange', ),
    0x0200: ('JPEGProc', ),
    0x0201: ('JPEGInterchangeFormat', ),
    0x0202: ('JPEGInterchangeFormatLength', ),
    0x0211: ('YCbCrCoefficients', ),
    0x0212: ('YCbCrSubSampling', ),
    0x0213: ('YCbCrPositioning', ),
    0x0214: ('ReferenceBlackWhite', ),
    0x828D: ('CFARepeatPatternDim', ),
    0x828E: ('CFAPattern', ),
    0x828F: ('BatteryLevel', ),
    0x8298: ('Copyright', ),
    0x829A: ('ExposureTime', ),
    0x829D: ('FNumber', ),
    0x83BB: ('IPTC/NAA', ),
    0x8769: ('ExifOffset', ),
    0x8773: ('InterColorProfile', ),
    0x8822: ('ExposureProgram',
             {0: 'Unidentified',
              1: 'Manual',
              2: 'Program Normal',
              3: 'Aperture Priority',
              4: 'Shutter Priority',
              5: 'Program Creative',
              6: 'Program Action',
              7: 'Portrait Mode',
              8: 'Landscape Mode'}),
    0x8824: ('SpectralSensitivity', ),
    0x8825: ('GPSInfo', ),
    0x8827: ('ISOSpeedRatings', ),
    0x8828: ('OECF', ),
    # print as string
    0x9000: ('ExifVersion', lambda x: ''.join(map(chr, x))),
    0x9003: ('DateTimeOriginal', ),
    0x9004: ('DateTimeDigitized', ),
    0x9101: ('ComponentsConfiguration',
             {0: '',
              1: 'Y',
              2: 'Cb',
              3: 'Cr',
              4: 'Red',
              5: 'Green',
              6: 'Blue'}),
    0x9102: ('CompressedBitsPerPixel', ),
    0x9201: ('ShutterSpeedValue', ),
    0x9202: ('ApertureValue', ),
    0x9203: ('BrightnessValue', ),
    0x9204: ('ExposureBiasValue', ),
    0x9205: ('MaxApertureValue', ),
    0x9206: ('SubjectDistance', ),
    0x9207: ('MeteringMode',
             {0: 'Unidentified',
              1: 'Average',
              2: 'CenterWeightedAverage',
              3: 'Spot',
              4: 'MultiSpot'}),
    0x9208: ('LightSource',
             {0:   'Unknown',
              1:   'Daylight',
              2:   'Fluorescent',
              3:   'Tungsten',
              10:  'Flash',
              17:  'Standard Light A',
              18:  'Standard Light B',
              19:  'Standard Light C',
              20:  'D55',
              21:  'D65',
              22:  'D75',
              255: 'Other'}),
    0x9209: ('Flash', {0:  'No',
                       1:  'Fired',
                       5:  'Fired (?)', # no return sensed
                       7:  'Fired (!)', # return sensed
                       9:  'Fill Fired',
                       13: 'Fill Fired (?)',
                       15: 'Fill Fired (!)',
                       16: 'Off',
                       24: 'Auto Off',
                       25: 'Auto Fired',
                       29: 'Auto Fired (?)',
                       31: 'Auto Fired (!)',
                       32: 'Not Available'}),
    0x920A: ('FocalLength', ),
    0x927C: ('MakerNote', ),
    # print as string
    0x9286: ('UserComment', lambda x: ''.join(map(chr, x))),
    0x9290: ('SubSecTime', ),
    0x9291: ('SubSecTimeOriginal', ),
    0x9292: ('SubSecTimeDigitized', ),
    # print as string
    0xA000: ('FlashPixVersion', lambda x: ''.join(map(chr, x))),
    0xA001: ('ColorSpace', ),
    0xA002: ('ExifImageWidth', ),
    0xA003: ('ExifImageLength', ),
    0xA005: ('InteroperabilityOffset', ),
    0xA20B: ('FlashEnergy', ),               # 0x920B in TIFF/EP
    0xA20C: ('SpatialFrequencyResponse', ),  # 0x920C    -  -
    0xA20E: ('FocalPlaneXResolution', ),     # 0x920E    -  -
    0xA20F: ('FocalPlaneYResolution', ),     # 0x920F    -  -
    0xA210: ('FocalPlaneResolutionUnit', ),  # 0x9210    -  -
    0xA214: ('SubjectLocation', ),           # 0x9214    -  -
    0xA215: ('ExposureIndex', ),             # 0x9215    -  -
    0xA217: ('SensingMethod', ),             # 0x9217    -  -
    0xA300: ('FileSource',
             {3: 'Digital Camera'}),
    0xA301: ('SceneType',
             {1: 'Directly Photographed'}),
    0xA302: ('CVAPattern',),
    }

# interoperability tags
INTR_TAGS={
    0x0001: ('InteroperabilityIndex', ),
    0x0002: ('InteroperabilityVersion', ),
    0x1000: ('RelatedImageFileFormat', ),
    0x1001: ('RelatedImageWidth', ),
    0x1002: ('RelatedImageLength', ),
    }

# GPS tags (not used yet, haven't seen camera with GPS)
GPS_TAGS={
    0x0000: ('GPSVersionID', ),
    0x0001: ('GPSLatitudeRef', ),
    0x0002: ('GPSLatitude', ),
    0x0003: ('GPSLongitudeRef', ),
    0x0004: ('GPSLongitude', ),
    0x0005: ('GPSAltitudeRef', ),
    0x0006: ('GPSAltitude', ),
    0x0007: ('GPSTimeStamp', ),
    0x0008: ('GPSSatellites', ),
    0x0009: ('GPSStatus', ),
    0x000A: ('GPSMeasureMode', ),
    0x000B: ('GPSDOP', ),
    0x000C: ('GPSSpeedRef', ),
    0x000D: ('GPSSpeed', ),
    0x000E: ('GPSTrackRef', ),
    0x000F: ('GPSTrack', ),
    0x0010: ('GPSImgDirectionRef', ),
    0x0011: ('GPSImgDirection', ),
    0x0012: ('GPSMapDatum', ),
    0x0013: ('GPSDestLatitudeRef', ),
    0x0014: ('GPSDestLatitude', ),
    0x0015: ('GPSDestLongitudeRef', ),
    0x0016: ('GPSDestLongitude', ),
    0x0017: ('GPSDestBearingRef', ),
    0x0018: ('GPSDestBearing', ),
    0x0019: ('GPSDestDistanceRef', ),
    0x001A: ('GPSDestDistance', )
    }

# Nikon E99x MakerNote Tags
# http://members.tripod.com/~tawba/990exif.htm
MAKERNOTE_NIKON_NEWER_TAGS={
    0x0002: ('ISOSetting', ),
    0x0003: ('ColorMode', ),
    0x0004: ('Quality', ),
    0x0005: ('Whitebalance', ),
    0x0006: ('ImageSharpening', ),
    0x0007: ('FocusMode', ),
    0x0008: ('FlashSetting', ),
    0x0009: ('AutoFlashMode', ),
    0x000B: ('WhiteBalanceBias', ),
    0x000C: ('WhiteBalanceRBCoeff', ),
    0x000F: ('ISOSelection', ),
    0x0012: ('FlashCompensation', ),
    0x0013: ('ISOSpeedRequested', ),
    0x0016: ('PhotoCornerCoordinates', ),
    0x0018: ('FlashBracketCompensationApplied', ),
    0x0019: ('AEBracketCompensationApplied', ),
    0x0080: ('ImageAdjustment', ),
    0x0081: ('ToneCompensation', ),
    0x0082: ('AuxiliaryLens', ),
    0x0083: ('LensType', ),
    0x0084: ('LensMinMaxFocalMaxAperture', ),
    0x0085: ('ManualFocusDistance', ),
    0x0086: ('DigitalZoomFactor', ),
    0x0088: ('AFFocusPosition',
             {0x0000: 'Center',
              0x0100: 'Top',
              0x0200: 'Bottom',
              0x0300: 'Left',
              0x0400: 'Right'}),
    0x0089: ('BracketingMode',
             {0x00: 'Single frame, no bracketing',
              0x01: 'Continuous, no bracketing',
              0x02: 'Timer, no bracketing',
              0x10: 'Single frame, exposure bracketing',
              0x11: 'Continuous, exposure bracketing',
              0x12: 'Timer, exposure bracketing',
              0x40: 'Single frame, white balance bracketing',
              0x41: 'Continuous, white balance bracketing',
              0x42: 'Timer, white balance bracketing'}),
    0x008D: ('ColorMode', ),
    0x008F: ('SceneMode?', ),
    0x0090: ('LightingType', ),
    0x0092: ('HueAdjustment', ),
    0x0094: ('Saturation',
             {-3: 'B&W',
              -2: '-2',
              -1: '-1',
              0:  '0',
              1:  '1',
              2:  '2'}),
    0x0095: ('NoiseReduction', ),
    0x00A7: ('TotalShutterReleases', ),
    0x00A9: ('ImageOptimization', ),
    0x00AA: ('Saturation', ),
    0x00AB: ('DigitalVariProgram', ),
    0x0010: ('DataDump', )
    }

MAKERNOTE_NIKON_OLDER_TAGS={
    0x0003: ('Quality',
             {1: 'VGA Basic',
              2: 'VGA Normal',
              3: 'VGA Fine',
              4: 'SXGA Basic',
              5: 'SXGA Normal',
              6: 'SXGA Fine'}),
    0x0004: ('ColorMode',
             {1: 'Color',
              2: 'Monochrome'}),
    0x0005: ('ImageAdjustment',
             {0: 'Normal',
              1: 'Bright+',
              2: 'Bright-',
              3: 'Contrast+',
              4: 'Contrast-'}),
    0x0006: ('CCDSpeed',
             {0: 'ISO 80',
              2: 'ISO 160',
              4: 'ISO 320',
              5: 'ISO 100'}),
    0x0007: ('WhiteBalance',
             {0: 'Auto',
              1: 'Preset',
              2: 'Daylight',
              3: 'Incandescent',
              4: 'Fluorescent',
              5: 'Cloudy',
              6: 'Speed Light'})
    }

# decode Olympus SpecialMode tag in MakerNote
def olympus_special_mode(v):
    a={
        0: 'Normal',
        1: 'Unknown',
        2: 'Fast',
        3: 'Panorama'}
    b={
        0: 'Non-panoramic',
        1: 'Left to right',
        2: 'Right to left',
        3: 'Bottom to top',
        4: 'Top to bottom'}
    return '%s - sequence %d - %s' % (a[v[0]], v[1], b[v[2]])
        
MAKERNOTE_OLYMPUS_TAGS={
    # ah HAH! those sneeeeeaky bastids! this is how they get past the fact
    # that a JPEG thumbnail is not allowed in an uncompressed TIFF file
    0x0100: ('JPEGThumbnail', ),
    0x0200: ('SpecialMode', olympus_special_mode),
    0x0201: ('JPEGQual',
             {1: 'SQ',
              2: 'HQ',
              3: 'SHQ'}),
    0x0202: ('Macro',
             {0: 'Normal',
              1: 'Macro'}),
    0x0204: ('DigitalZoom', ),
    0x0207: ('SoftwareRelease',  ),
    0x0208: ('PictureInfo',  ),
    # print as string
    0x0209: ('CameraID', lambda x: ''.join(map(chr, x))),
    0x0F00: ('DataDump',  )
    }

MAKERNOTE_CASIO_TAGS={
    0x0001: ('RecordingMode',
             {1: 'Single Shutter',
              2: 'Panorama',
              3: 'Night Scene',
              4: 'Portrait',
              5: 'Landscape'}),
    0x0002: ('Quality',
             {1: 'Economy',
              2: 'Normal',
              3: 'Fine'}),
    0x0003: ('FocusingMode',
             {2: 'Macro',
              3: 'Auto Focus',
              4: 'Manual Focus',
              5: 'Infinity'}),
    0x0004: ('FlashMode',
             {1: 'Auto',
              2: 'On',
              3: 'Off',
              4: 'Red Eye Reduction'}),
    0x0005: ('FlashIntensity',
             {11: 'Weak',
              13: 'Normal',
              15: 'Strong'}),
    0x0006: ('Object Distance', ),
    0x0007: ('WhiteBalance',
             {1:   'Auto',
              2:   'Tungsten',
              3:   'Daylight',
              4:   'Fluorescent',
              5:   'Shade',
              129: 'Manual'}),
    0x000B: ('Sharpness',
             {0: 'Normal',
              1: 'Soft',
              2: 'Hard'}),
    0x000C: ('Contrast',
             {0: 'Normal',
              1: 'Low',
              2: 'High'}),
    0x000D: ('Saturation',
             {0: 'Normal',
              1: 'Low',
              2: 'High'}),
    0x0014: ('CCDSpeed',
             {64:  'Normal',
              80:  'Normal',
              100: 'High',
              125: '+1.0',
              244: '+3.0',
              250: '+2.0',})
    }

MAKERNOTE_FUJIFILM_TAGS={
    0x0000: ('NoteVersion', lambda x: ''.join(map(chr, x))),
    0x1000: ('Quality', ),
    0x1001: ('Sharpness',
             {1: 'Soft',
              2: 'Soft',
              3: 'Normal',
              4: 'Hard',
              5: 'Hard'}),
    0x1002: ('WhiteBalance',
             {0:    'Auto',
              256:  'Daylight',
              512:  'Cloudy',
              768:  'DaylightColor-Fluorescent',
              769:  'DaywhiteColor-Fluorescent',
              770:  'White-Fluorescent',
              1024: 'Incandescent',
              3840: 'Custom'}),
    0x1003: ('Color',
             {0:   'Normal',
              256: 'High',
              512: 'Low'}),
    0x1004: ('Tone',
             {0:   'Normal',
              256: 'High',
              512: 'Low'}),
    0x1010: ('FlashMode',
             {0: 'Auto',
              1: 'On',
              2: 'Off',
              3: 'Red Eye Reduction'}),
    0x1011: ('FlashStrength', ),
    0x1020: ('Macro',
             {0: 'Off',
              1: 'On'}),
    0x1021: ('FocusMode',
             {0: 'Auto',
              1: 'Manual'}),
    0x1030: ('SlowSync',
             {0: 'Off',
              1: 'On'}),
    0x1031: ('PictureMode',
             {0:   'Auto',
              1:   'Portrait',
              2:   'Landscape',
              4:   'Sports',
              5:   'Night',
              6:   'Program AE',
              256: 'Aperture Priority AE',
              512: 'Shutter Priority AE',
              768: 'Manual Exposure'}),
    0x1100: ('MotorOrBracket',
             {0: 'Off',
              1: 'On'}),
    0x1300: ('BlurWarning',
             {0: 'Off',
              1: 'On'}),
    0x1301: ('FocusWarning',
             {0: 'Off',
              1: 'On'}),
    0x1302: ('AEWarning',
             {0: 'Off',
              1: 'On'})
    }

MAKERNOTE_CANON_TAGS={
    0x0006: ('ImageType', ),
    0x0007: ('FirmwareVersion', ),
    0x0008: ('ImageNumber', ),
    0x0009: ('OwnerName', )
    }

# see http://www.burren.cx/david/canon.html by David Burren
# this is in element offset, name, optional value dictionary format
MAKERNOTE_CANON_TAG_0x001={
    1: ('Macromode',
        {1: 'Macro',
         2: 'Normal'}),
    2: ('SelfTimer', ),
    3: ('Quality',
        {2: 'Normal',
         3: 'Fine',
         5: 'Superfine'}),
    4: ('FlashMode',
        {0: 'Flash Not Fired',
         1: 'Auto',
         2: 'On',
         3: 'Red-Eye Reduction',
         4: 'Slow Synchro',
         5: 'Auto + Red-Eye Reduction',
         6: 'On + Red-Eye Reduction',
         16: 'external flash'}),
    5: ('ContinuousDriveMode',
        {0: 'Single Or Timer',
         1: 'Continuous'}),
    7: ('FocusMode',
        {0: 'One-Shot',
         1: 'AI Servo',
         2: 'AI Focus',
         3: 'MF',
         4: 'Single',
         5: 'Continuous',
         6: 'MF'}),
    10: ('ImageSize',
         {0: 'Large',
          1: 'Medium',
          2: 'Small'}),
    11: ('EasyShootingMode',
         {0: 'Full Auto',
          1: 'Manual',
          2: 'Landscape',
          3: 'Fast Shutter',
          4: 'Slow Shutter',
          5: 'Night',
          6: 'B&W',
          7: 'Sepia',
          8: 'Portrait',
          9: 'Sports',
          10: 'Macro/Close-Up',
          11: 'Pan Focus'}),
    12: ('DigitalZoom',
         {0: 'None',
          1: '2x',
          2: '4x'}),
    13: ('Contrast',
         {0xFFFF: 'Low',
          0: 'Normal',
          1: 'High'}),
    14: ('Saturation',
         {0xFFFF: 'Low',
          0: 'Normal',
          1: 'High'}),
    15: ('Sharpness',
         {0xFFFF: 'Low',
          0: 'Normal',
          1: 'High'}),
    16: ('ISO',
         {0: 'See ISOSpeedRatings Tag',
          15: 'Auto',
          16: '50',
          17: '100',
          18: '200',
          19: '400'}),
    17: ('MeteringMode',
         {3: 'Evaluative',
          4: 'Partial',
          5: 'Center-weighted'}),
    18: ('FocusType',
         {0: 'Manual',
          1: 'Auto',
          3: 'Close-Up (Macro)',
          8: 'Locked (Pan Mode)'}),
    19: ('AFPointSelected',
         {0x3000: 'None (MF)',
          0x3001: 'Auto-Selected',
          0x3002: 'Right',
          0x3003: 'Center',
          0x3004: 'Left'}),
    20: ('ExposureMode',
         {0: 'Easy Shooting',
          1: 'Program',
          2: 'Tv-priority',
          3: 'Av-priority',
          4: 'Manual',
          5: 'A-DEP'}),
    23: ('LongFocalLengthOfLensInFocalUnits', ),
    24: ('ShortFocalLengthOfLensInFocalUnits', ),
    25: ('FocalUnitsPerMM', ),
    28: ('FlashActivity',
         {0: 'Did Not Fire',
          1: 'Fired'}),
    29: ('FlashDetails',
         {14: 'External E-TTL',
          13: 'Internal Flash',
          11: 'FP Sync Used',
          7: '2nd("Rear")-Curtain Sync Used',
          4: 'FP Sync Enabled'}),
    32: ('FocusMode',
         {0: 'Single',
          1: 'Continuous'})
    }

MAKERNOTE_CANON_TAG_0x004={
    7: ('WhiteBalance',
        {0: 'Auto',
         1: 'Sunny',
         2: 'Cloudy',
         3: 'Tungsten',
         4: 'Fluorescent',
         5: 'Flash',
         6: 'Custom'}),
    9: ('SequenceNumber', ),
    14: ('AFPointUsed', ),
    15: ('FlashBias',
        {0XFFC0: '-2 EV',
         0XFFCC: '-1.67 EV',
         0XFFD0: '-1.50 EV',
         0XFFD4: '-1.33 EV',
         0XFFE0: '-1 EV',
         0XFFEC: '-0.67 EV',
         0XFFF0: '-0.50 EV',
         0XFFF4: '-0.33 EV',
         0X0000: '0 EV',
         0X000C: '0.33 EV',
         0X0010: '0.50 EV',
         0X0014: '0.67 EV',
         0X0020: '1 EV',
         0X002C: '1.33 EV',
         0X0030: '1.50 EV',
         0X0034: '1.67 EV',
         0X0040: '2 EV'}),
    19: ('SubjectDistance', )
    }

# extract multibyte integer in Motorola format (little endian)
def s2n_motorola(str):
    x=0
    for c in str:
        x=(x << 8) | ord(c)
    return x

# extract multibyte integer in Intel format (big endian)
def s2n_intel(str):
    x=0
    y=0L
    for c in str:
        x=x | (ord(c) << y)
        y=y+8
    return x

# ratio object that eventually will be able to reduce itself to lowest
# common denominator for printing
def gcd(a, b):
   if b == 0:
      return a
   else:
      return gcd(b, a % b)

class Ratio:
    def __init__(self, num, den):
        self.num=num
        self.den=den

    def __repr__(self):
        self.reduce()
        if self.den == 1:
            return str(self.num)
        return '%d/%d' % (self.num, self.den)

    def reduce(self):
        div=gcd(self.num, self.den)
        if div > 1:
            self.num=self.num/div
            self.den=self.den/div

# for ease of dealing with tags
class IFD_Tag:
    def __init__(self, printable, tag, field_type, values, field_offset,
                 field_length):
        # printable version of data
        self.printable=printable
        # tag ID number
        self.tag=tag
        # field type as index into FIELD_TYPES
        self.field_type=field_type
        # offset of start of field in bytes from beginning of IFD
        self.field_offset=field_offset
        # length of data field in bytes
        self.field_length=field_length
        # either a string or array of data items
        self.values=values
        
    def __str__(self):
        return self.printable
    
    def __repr__(self):
        return '(0x%04X) %s=%s @ %d' % (self.tag,
                                        FIELD_TYPES[self.field_type][2],
                                        self.printable,
                                        self.field_offset)

# class that handles an EXIF header
class EXIF_header:
    def __init__(self, file, endian, offset, fake_exif, debug=0):
        self.file=file
        self.endian=endian
        self.offset=offset
        self.fake_exif=fake_exif
        self.debug=debug
        self.tags={}
        
    # convert slice to integer, based on sign and endian flags
    # usually this offset is assumed to be relative to the beginning of the
    # start of the EXIF information.  For some cameras that use relative tags,
    # this offset may be relative to some other starting point.
    def s2n(self, offset, length, signed=0):
        self.file.seek(self.offset+offset)
        slice=self.file.read(length)
        if self.endian == 'I':
            val=s2n_intel(slice)
        else:
            val=s2n_motorola(slice)
        # Sign extension ?
        if signed:
            msb=1L << (8*length-1)
            if val & msb:
                val=val-(msb << 1)
        return val

    # convert offset to string
    def n2s(self, offset, length):
        s=''
        for i in range(length):
            if self.endian == 'I':
                s=s+chr(offset & 0xFF)
            else:
                s=chr(offset & 0xFF)+s
            offset=offset >> 8
        return s
    
    # return first IFD
    def first_IFD(self):
        return self.s2n(4, 4)

    # return pointer to next IFD
    def next_IFD(self, ifd):
        entries=self.s2n(ifd, 2)
        return self.s2n(ifd+2+12*entries, 4)

    # return list of IFDs in header
    def list_IFDs(self):
        i=self.first_IFD()
        a=[]
        while i:
            a.append(i)
            i=self.next_IFD(i)
        return a

    # return list of entries in this IFD
    def dump_IFD(self, ifd, ifd_name, dict=EXIF_TAGS, relative=0):
        entries=self.s2n(ifd, 2)
        for i in range(entries):
            # entry is index of start of this IFD in the file
            entry=ifd+2+12*i
            tag=self.s2n(entry, 2)
            # get tag name.  We do it early to make debugging easier
            tag_entry=dict.get(tag)
            if tag_entry:
                tag_name=tag_entry[0]
            else:
                tag_name='Tag 0x%04X' % tag
            field_type=self.s2n(entry+2, 2)
            if not 0 < field_type < len(FIELD_TYPES):
                # unknown field type
                raise ValueError, \
                      'unknown type %d in tag 0x%04X' % (field_type, tag)
            typelen=FIELD_TYPES[field_type][0]
            count=self.s2n(entry+4, 4)
            offset=entry+8
            if count*typelen > 4:
                # offset is not the value; it's a pointer to the value
                # if relative we set things up so s2n will seek to the right
                # place when it adds self.offset.  Note that this 'relative'
                # is for the Nikon type 3 makernote.  Other cameras may use
                # other relative offsets, which would have to be computed here
                # slightly differently.
                if relative:
                    tmp_offset=self.s2n(offset, 4)
                    offset=tmp_offset+ifd-self.offset+4
                    if self.fake_exif:
                        offset=offset+18
                else:
                    offset=self.s2n(offset, 4)
            field_offset=offset
            if field_type == 2:
                # special case: null-terminated ASCII string
                if count != 0:
                    self.file.seek(self.offset+offset)
                    values=self.file.read(count)
                    values=values.strip().replace('\x00','')
                else:
                    values=''
            else:
                values=[]
                signed=(field_type in [6, 8, 9, 10])
                for j in range(count):
                    if field_type in (5, 10):
                        # a ratio
                        value_j=Ratio(self.s2n(offset,   4, signed),
                                      self.s2n(offset+4, 4, signed))
                    else:
                        value_j=self.s2n(offset, typelen, signed)
                    values.append(value_j)
                    offset=offset+typelen
            # now "values" is either a string or an array
            if count == 1 and field_type != 2:
                printable=str(values[0])
            else:
                printable=str(values)
            # compute printable version of values
            if tag_entry:
                if len(tag_entry) != 1:
                    # optional 2nd tag element is present
                    if callable(tag_entry[1]):
                        # call mapping function
                        printable=tag_entry[1](values)
                    else:
                        printable=''
                        for i in values:
                            # use lookup table for this tag
                            printable+=tag_entry[1].get(i, repr(i))
            self.tags[ifd_name+' '+tag_name]=IFD_Tag(printable, tag,
                                                     field_type,
                                                     values, field_offset,
                                                     count*typelen)
            if self.debug:
                print ' debug:   %s: %s' % (tag_name,
                                            repr(self.tags[ifd_name+' '+tag_name]))

    # extract uncompressed TIFF thumbnail (like pulling teeth)
    # we take advantage of the pre-existing layout in the thumbnail IFD as
    # much as possible
    def extract_TIFF_thumbnail(self, thumb_ifd):
        entries=self.s2n(thumb_ifd, 2)
        # this is header plus offset to IFD ...
        if self.endian == 'M':
            tiff='MM\x00*\x00\x00\x00\x08'
        else:
            tiff='II*\x00\x08\x00\x00\x00'
        # ... plus thumbnail IFD data plus a null "next IFD" pointer
        self.file.seek(self.offset+thumb_ifd)
        tiff+=self.file.read(entries*12+2)+'\x00\x00\x00\x00'
        
        # fix up large value offset pointers into data area
        for i in range(entries):
            entry=thumb_ifd+2+12*i
            tag=self.s2n(entry, 2)
            field_type=self.s2n(entry+2, 2)
            typelen=FIELD_TYPES[field_type][0]
            count=self.s2n(entry+4, 4)
            oldoff=self.s2n(entry+8, 4)
            # start of the 4-byte pointer area in entry
            ptr=i*12+18
            # remember strip offsets location
            if tag == 0x0111:
                strip_off=ptr
                strip_len=count*typelen
            # is it in the data area?
            if count*typelen > 4:
                # update offset pointer (nasty "strings are immutable" crap)
                # should be able to say "tiff[ptr:ptr+4]=newoff"
                newoff=len(tiff)
                tiff=tiff[:ptr]+self.n2s(newoff, 4)+tiff[ptr+4:]
                # remember strip offsets location
                if tag == 0x0111:
                    strip_off=newoff
                    strip_len=4
                # get original data and store it
                self.file.seek(self.offset+oldoff)
                tiff+=self.file.read(count*typelen)
                
        # add pixel strips and update strip offset info
        old_offsets=self.tags['Thumbnail StripOffsets'].values
        old_counts=self.tags['Thumbnail StripByteCounts'].values
        for i in range(len(old_offsets)):
            # update offset pointer (more nasty "strings are immutable" crap)
            offset=self.n2s(len(tiff), strip_len)
            tiff=tiff[:strip_off]+offset+tiff[strip_off+strip_len:]
            strip_off+=strip_len
            # add pixel strip to end
            self.file.seek(self.offset+old_offsets[i])
            tiff+=self.file.read(old_counts[i])
            
        self.tags['TIFFThumbnail']=tiff
        
    # decode all the camera-specific MakerNote formats

    # Note is the data that comprises this MakerNote.  The MakerNote will
    # likely have pointers in it that point to other parts of the file.  We'll
    # use self.offset as the starting point for most of those pointers, since
    # they are relative to the beginning of the file.
    #
    # If the MakerNote is in a newer format, it may use relative addressing
    # within the MakerNote.  In that case we'll use relative addresses for the
    # pointers.
    #
    # As an aside: it's not just to be annoying that the manufacturers use
    # relative offsets.  It's so that if the makernote has to be moved by the
    # picture software all of the offsets don't have to be adjusted.  Overall,
    # this is probably the right strategy for makernotes, though the spec is
    # ambiguous.  (The spec does not appear to imagine that makernotes would
    # follow EXIF format internally.  Once they did, it's ambiguous whether
    # the offsets should be from the header at the start of all the EXIF info,
    # or from the header at the start of the makernote.)
    def decode_maker_note(self):
        note=self.tags['EXIF MakerNote']
        make=self.tags['Image Make'].printable
        model=self.tags['Image Model'].printable

        # Nikon
        # The maker note usually starts with the word Nikon, followed by the
        # type of the makernote (1 or 2, as a short).  If the word Nikon is
        # not at the start of the makernote, it's probably type 2, since some
        # cameras work that way.
        if make in ('NIKON', 'NIKON CORPORATION'):
            if note.values[0:7] == [78, 105, 107, 111, 110, 00, 01]:
                if self.debug:
                    print "Looks like a type 1 Nikon MakerNote."
                self.dump_IFD(note.field_offset+8, 'MakerNote',
                              dict=MAKERNOTE_NIKON_OLDER_TAGS)
            elif note.values[0:7] == [78, 105, 107, 111, 110, 00, 02]:
                if self.debug:
                    print "Looks like a labeled type 2 Nikon MakerNote"
                if note.values[12:14] != [0, 42] and note.values[12:14] != [42L, 0L]:
                    raise ValueError, "Missing marker tag '42' in MakerNote."
                # skip the Makernote label and the TIFF header
                self.dump_IFD(note.field_offset+10+8, 'MakerNote',
                              dict=MAKERNOTE_NIKON_NEWER_TAGS, relative=1)
            else:
                # E99x or D1
                if self.debug:
                    print "Looks like an unlabeled type 2 Nikon MakerNote"
                self.dump_IFD(note.field_offset, 'MakerNote',
                              dict=MAKERNOTE_NIKON_NEWER_TAGS)
            return

        # Olympus
        if make[:7] == 'OLYMPUS':
            self.dump_IFD(note.field_offset+8, 'MakerNote',
                          dict=MAKERNOTE_OLYMPUS_TAGS)
            return

        # Casio
        if make == 'Casio':
            self.dump_IFD(note.field_offset, 'MakerNote',
                          dict=MAKERNOTE_CASIO_TAGS)
            return
        
        # Fujifilm
        if make == 'FUJIFILM':
            # bug: everything else is "Motorola" endian, but the MakerNote
            # is "Intel" endian
            endian=self.endian
            self.endian='I'
            # bug: IFD offsets are from beginning of MakerNote, not
            # beginning of file header
            offset=self.offset
            self.offset+=note.field_offset
            # process note with bogus values (note is actually at offset 12)
            self.dump_IFD(12, 'MakerNote', dict=MAKERNOTE_FUJIFILM_TAGS)
            # reset to correct values
            self.endian=endian
            self.offset=offset
            return
        
        # Canon
        if make == 'Canon':
            self.dump_IFD(note.field_offset, 'MakerNote',
                          dict=MAKERNOTE_CANON_TAGS)
            for i in (('MakerNote Tag 0x0001', MAKERNOTE_CANON_TAG_0x001),
                      ('MakerNote Tag 0x0004', MAKERNOTE_CANON_TAG_0x004)):
                self.canon_decode_tag(self.tags[i[0]].values, i[1])
            return

    # decode Canon MakerNote tag based on offset within tag
    # see http://www.burren.cx/david/canon.html by David Burren
    def canon_decode_tag(self, value, dict):
        for i in range(1, len(value)):
            x=dict.get(i, ('Unknown', ))
            if self.debug:
                print i, x
            name=x[0]
            if len(x) > 1:
                val=x[1].get(value[i], 'Unknown')
            else:
                val=value[i]
            # it's not a real IFD Tag but we fake one to make everybody
            # happy. this will have a "proprietary" type
            self.tags['MakerNote '+name]=IFD_Tag(str(val), None, 0, None,
                                                 None, None)

# process an image file (expects an open file object)
# this is the function that has to deal with all the arbitrary nasty bits
# of the EXIF standard
def process_file(file, debug=0):
    # determine whether it's a JPEG or TIFF
    data=file.read(12)
    if data[0:4] in ['II*\x00', 'MM\x00*']:
        # it's a TIFF file
        file.seek(0)
        endian=file.read(1)
        file.read(1)
        offset=0
    elif data[0:2] == '\xFF\xD8':
        # it's a JPEG file
        # skip JFIF style header(s)
        fake_exif=0
        while data[2] == '\xFF' and data[6:10] in ('JFIF', 'JFXX', 'OLYM'):
            length=ord(data[4])*256+ord(data[5])
            file.read(length-8)
            # fake an EXIF beginning of file
            data='\xFF\x00'+file.read(10)
            fake_exif=1
        if data[2] == '\xFF' and data[6:10] == 'Exif':
            # detected EXIF header
            offset=file.tell()
            endian=file.read(1)
        else:
            # no EXIF information
            return {}
    else:
        # file format not recognized
        return {}

    # deal with the EXIF info we found
    if debug:
        print {'I': 'Intel', 'M': 'Motorola'}[endian], 'format'
    hdr=EXIF_header(file, endian, offset, fake_exif, debug)
    ifd_list=hdr.list_IFDs()
    ctr=0
    for i in ifd_list:
        if ctr == 0:
            IFD_name='Image'
        elif ctr == 1:
            IFD_name='Thumbnail'
            thumb_ifd=i
        else:
            IFD_name='IFD %d' % ctr
        if debug:
            print ' IFD %d (%s) at offset %d:' % (ctr, IFD_name, i)
        hdr.dump_IFD(i, IFD_name)
        # EXIF IFD
        exif_off=hdr.tags.get(IFD_name+' ExifOffset')
        if exif_off:
            if debug:
                print ' EXIF SubIFD at offset %d:' % exif_off.values[0]
            hdr.dump_IFD(exif_off.values[0], 'EXIF')
            # Interoperability IFD contained in EXIF IFD
            intr_off=hdr.tags.get('EXIF SubIFD InteroperabilityOffset')
            if intr_off:
                if debug:
                    print ' EXIF Interoperability SubSubIFD at offset %d:' \
                          % intr_off.values[0]
                hdr.dump_IFD(intr_off.values[0], 'EXIF Interoperability',
                             dict=INTR_TAGS)
        # GPS IFD
        gps_off=hdr.tags.get(IFD_name+' GPSInfo')
        if gps_off:
            if debug:
                print ' GPS SubIFD at offset %d:' % gps_off.values[0]
            hdr.dump_IFD(gps_off.values[0], 'GPS', dict=GPS_TAGS)
        ctr+=1

    # extract uncompressed TIFF thumbnail
    thumb=hdr.tags.get('Thumbnail Compression')
    if thumb and thumb.printable == 'Uncompressed TIFF':
        hdr.extract_TIFF_thumbnail(thumb_ifd)
        
    # JPEG thumbnail (thankfully the JPEG data is stored as a unit)
    thumb_off=hdr.tags.get('Thumbnail JPEGInterchangeFormat')
    if thumb_off:
        file.seek(offset+thumb_off.values[0])
        size=hdr.tags['Thumbnail JPEGInterchangeFormatLength'].values[0]
        hdr.tags['JPEGThumbnail']=file.read(size)
        
    # deal with MakerNote contained in EXIF IFD
    if hdr.tags.has_key('EXIF MakerNote'):
        hdr.decode_maker_note()

    # Sometimes in a TIFF file, a JPEG thumbnail is hidden in the MakerNote
    # since it's not allowed in a uncompressed TIFF IFD
    if not hdr.tags.has_key('JPEGThumbnail'):
        thumb_off=hdr.tags.get('MakerNote JPEGThumbnail')
        if thumb_off:
            file.seek(offset+thumb_off.values[0])
            hdr.tags['JPEGThumbnail']=file.read(thumb_off.field_length)
            
    return hdr.tags

# library test/debug function (dump given files)
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print 'Usage: %s files...\n' % sys.argv[0]
        sys.exit(0)
        
    for filename in sys.argv[1:]:
        try:
            file=open(filename, 'rb')
        except:
            print filename, 'unreadable'
            print
            continue
        print filename+':'
        # data=process_file(file, 1) # with debug info
        data=process_file(file)
        if not data:
            print 'No EXIF information found'
            continue

        x=data.keys()
        x.sort()
        for i in x:
            if i in ('JPEGThumbnail', 'TIFFThumbnail'):
                continue
            try:
                print '   %s (%s): %s' % \
                      (i, FIELD_TYPES[data[i].field_type][2], data[i].printable)
            except:
                print 'error', i, '"', data[i], '"'
        if data.has_key('JPEGThumbnail'):
            print 'File has JPEG thumbnail'
        print
