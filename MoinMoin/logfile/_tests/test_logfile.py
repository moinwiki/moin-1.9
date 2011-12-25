# -*- coding: utf-8 -*-
"""
    MoinMoin - MoinMoin.logfile Tests

    @copyright: 2011 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""
import os
import tempfile
import shutil
from StringIO import StringIO

from MoinMoin.logfile import LogFile


class TestLogFile(object):
    """ testing logfile reading/writing """
    # mtime rev action pagename host hostname user_id extra comment
    LOG = [
           [u'1292630945000000', u'00000001', u'SAVENEW', u'foo', u'0.0.0.0', u'example.org', u'111.111.111', u'', u''],
           [u'1292630957849084', u'99999999', u'ATTNEW', u'foo', u'0.0.0.0', u'example.org', u'222.222.222', u'file.txt', u''],
           [u'1292680177309091', u'99999999', u'ATTDEL', u'foo', u'0.0.0.0', u'example.org', u'333.333.333', u'file.txt', u''],
           [u'1292680233866579', u'99999999', u'ATTNEW', u'foo', u'0.0.0.0', u'example.org', u'444.444.444', u'new.tgz', u''],
           [u'1303073723000000', u'00000002', u'SAVE', u'foo', u'0.0.0.0', u'example.org', u'555.555.555', u'', u''],
          ]

    def make_line(self, linedata):
        line = u'\t'.join(linedata) + u'\n'
        return line.encode('utf-8')

    def write_log(self, fname, data):
        f = open(fname, "wb")
        for linedata in data:
            f.write(self.make_line(linedata))
        f.close()

    def setup_method(self, method):
        self.fname = tempfile.mktemp()
        self.write_log(self.fname, self.LOG)

    def teardown_method(self, method):
        os.remove(self.fname)

    def test_add(self):
        fname_log = tempfile.mktemp()
        lf = LogFile(fname_log)
        for linedata in self.LOG:
            lf.add(*linedata)
        expected_contents = open(self.fname, 'rb').read()
        real_contents = open(fname_log, 'rb').read()
        print repr(expected_contents)
        print repr(real_contents)
        assert real_contents == expected_contents

    def test_iter_forward(self):
        lf = LogFile(self.fname)
        for result, expected in zip(lf, self.LOG):
            print expected
            print result
            assert result == expected

    def test_iter_reverse(self):
        lf = LogFile(self.fname)
        for result, expected in zip(lf.reverse(), self.LOG[::-1]):
            print expected
            print result
            assert result == expected

    def test_position(self):
        lf = LogFile(self.fname)
        expected_pos = 0
        for data in lf:
            expected_pos += len(self.make_line(data))
            real_pos = lf.position()
            print expected_pos, real_pos
            assert real_pos == expected_pos

    def test_seek(self):
        lf = LogFile(self.fname)
        for data in lf:
            print repr(data)
        # now we are at the current end, remember position
        pos = lf.position()
        # add new data
        newdata = [u'1303333333000000', u'00000003', u'SAVE', u'foo', u'0.0.0.0', u'example.org', u'666.666.666', u'', u'comment']
        lf.add(*newdata)
        # go to position before new data
        lf.seek(pos)
        assert lf.position() == pos
        for data in lf:
            # reads the one new line we added
            print 'new:', repr(data)
            assert data == newdata
        lf.seek(0)
        assert lf.position() == 0
        assert list(lf) == self.LOG + [newdata]

coverage_modules = ['MoinMoin.logfile']

