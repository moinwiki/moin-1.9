# -*- coding: iso-8859-1 -*-
"""
    thfcgi.py - FastCGI communication with thread support

    Copyright Peter Åstrand <astrand@lysator.liu.se> 2001

    Modified for MoinMoin by Oliver Graf <ograf@bitart.de> 2003
    
    Added "external application" support, refactored code
        by Alexander Schremmer <alex AT alexanderweb DOT de>

    Cleanup, fixed typos, PEP-8, support for limiting creation of threads,
    limited number of requests lifetime, configurable backlog for socket
    .listen() by MoinMoin:ThomasWaldmann.

    2007 Support for Python's logging module by MoinMoin:ThomasWaldmann.

    For code base see:
    http://cvs.lysator.liu.se/viewcvs/viewcvs.cgi/webkom/thfcgi.py?cvsroot=webkom

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; version 2 of the License. 

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
"""

# TODO: Compare compare the number of bytes received on FCGI_STDIN with
#       CONTENT_LENGTH and abort the update if the two numbers are not equal.

import logging
log = logging.getLogger(__name__)

import os
import sys
import select
import socket
import errno
import cgi
from cStringIO import StringIO
import struct

try:
    import threading as _threading
except ImportError:
    import dummy_threading as _threading

# Maximum number of requests that can be handled
FCGI_MAX_REQS = 50
FCGI_MAX_CONNS = 50
FCGI_VERSION_1 = 1

# Can this application multiplex connections?
FCGI_MPXS_CONNS = 0

# Record types
FCGI_BEGIN_REQUEST = 1
FCGI_ABORT_REQUEST = 2
FCGI_END_REQUEST = 3
FCGI_PARAMS = 4
FCGI_STDIN = 5
FCGI_STDOUT = 6
FCGI_STDERR = 7
FCGI_DATA = 8
FCGI_GET_VALUES = 9
FCGI_GET_VALUES_RESULT = 10
FCGI_UNKNOWN_TYPE = 11
FCGI_MAXTYPE = FCGI_UNKNOWN_TYPE

# Types of management records
KNOWN_MANAGEMENT_TYPES = [FCGI_GET_VALUES]

FCGI_NULL_REQUEST_ID = 0

# Masks for flags component of FCGI_BEGIN_REQUEST
FCGI_KEEP_CONN = 1

# Values for role component of FCGI_BEGIN_REQUEST
FCGI_RESPONDER = 1
FCGI_AUTHORIZER = 2
FCGI_FILTER = 3

# Values for protocolStatus component of FCGI_END_REQUEST
FCGI_REQUEST_COMPLETE = 0     # Request completed ok
FCGI_CANT_MPX_CONN = 1        # This app cannot multiplex
FCGI_OVERLOADED = 2           # Too busy
FCGI_UNKNOWN_ROLE = 3         # Role value not known

# Struct format types
FCGI_BeginRequestBody = "!HB5x"
FCGI_Record_header = "!BBHHBx"
FCGI_UnknownTypeBody = "!B7x"
FCGI_EndRequestBody = "!IB3x"


def log(s):
    logging.debug(s)

class SocketErrorOnWrite:
    """Is raised if a write fails in the socket code."""
    pass

class Record:
    """Class representing FastCGI records"""

    def __init__(self):
        """Initialize FastCGI record"""
        self.version = FCGI_VERSION_1
        self.rec_type = FCGI_UNKNOWN_TYPE
        self.req_id   = FCGI_NULL_REQUEST_ID
        self.content = ""

        # Only in FCGI_BEGIN_REQUEST
        self.role = None
        self.flags = None
        self.keep_conn = 0

        # Only in FCGI_UNKNOWN_TYPE
        self.unknownType = None

        # Only in FCGI_END_REQUEST
        self.appStatus = None
        self.protocolStatus = None

    def read_pair(self, data, pos):
        """Read a FastCGI key-value pair from the server."""
        namelen = struct.unpack("!B", data[pos])[0]
        if namelen & 128:
            # 4-byte name length
            namelen = struct.unpack("!I", data[pos:pos+4])[0] & 0x7fffffff
            pos += 4
        else:
            pos += 1

        valuelen = struct.unpack("!B", data[pos])[0]
        if valuelen & 128:
            # 4-byte value length
            valuelen = struct.unpack("!I", data[pos:pos+4])[0] & 0x7fffffff
            pos += 4
        else:
            pos += 1

        name = data[pos:pos+namelen]
        pos += namelen
        value = data[pos:pos+valuelen]
        pos += valuelen

        return name, value, pos

    def write_pair(self, name, value):
        """Write a FastCGI key-value pair to the server."""
        namelen = len(name)
        if namelen < 128:
            data = struct.pack("!B", namelen)
        else:
            # 4-byte name length
            data = struct.pack("!I", namelen | 0x80000000L)

        valuelen = len(value)
        if valuelen < 128:
            data += struct.pack("!B", value)
        else:
            # 4-byte value length
            data += struct.pack("!I", value | 0x80000000L)

        return data + name + value

    def readRecord(self, sock):
        """Read a FastCGI record from the server."""
        data = sock.recv(8)
        if not data:
            # No data received. This means EOF. 
            return None

        self.version, self.rec_type, self.req_id, contentLength, paddingLength = \
            struct.unpack(FCGI_Record_header, data)

        self.content = ""
        while len(self.content) < contentLength:
            data = sock.recv(contentLength - len(self.content))
            self.content = self.content + data
        if paddingLength != 0:
            sock.recv(paddingLength)

        # Parse the content information
        if self.rec_type == FCGI_BEGIN_REQUEST:
            self.role, self.flags = struct.unpack(FCGI_BeginRequestBody, self.content)
            self.keep_conn = self.flags & FCGI_KEEP_CONN

        elif self.rec_type == FCGI_UNKNOWN_TYPE:
            self.unknownType = struct.unpack(FCGI_UnknownTypeBody, self.content)

        elif self.rec_type == FCGI_GET_VALUES or self.rec_type == FCGI_PARAMS:
            self.values = {}
            pos = 0
            while pos < len(self.content):
                name, value, pos = self.read_pair(self.content, pos)
                self.values[name] = value

        elif self.rec_type == FCGI_END_REQUEST:
            self.appStatus, self.protocolStatus = struct.unpack(FCGI_EndRequestBody, self.content)

        return 1

    def writeRecord(self, sock):
        """Write a FastCGI record to the server."""
        content = self.content
        if self.rec_type == FCGI_BEGIN_REQUEST:
            content = struct.pack(FCGI_BeginRequestBody, self.role, self.flags)

        elif self.rec_type == FCGI_UNKNOWN_TYPE:
            content = struct.pack(FCGI_UnknownTypeBody, self.unknownType)

        elif self.rec_type == FCGI_GET_VALUES or self.rec_type == FCGI_PARAMS:
            content = ""
            for i in self.values:
                content = content + self.write_pair(i, self.values[i])

        elif self.rec_type == FCGI_END_REQUEST:
            content = struct.pack(FCGI_EndRequestBody, self.appStatus, self.protocolStatus)

        # Align to 8-byte boundary
        clen = len(content)
        padlen = ((clen + 7) & 0xfff8) - clen

        hdr = struct.pack(FCGI_Record_header, self.version, self.rec_type, self.req_id, clen, padlen)

        try:
            sock.sendall(hdr + content + padlen*"\x00")
        except socket.error:
            # Write error, probably broken pipe. Exit. 
            raise SocketErrorOnWrite


class Request:
    """A request, corresponding to an accept():ed connection and
    a FCGI request."""

    def __init__(self, conn, req_handler, inthread=False):
        """Initialize Request container."""
        self.conn = conn
        self.req_handler = req_handler
        self.inthread = inthread

        self.keep_conn = 0
        self.req_id = None

        # Input
        self.env = {}
        self.env_complete = 0
        self.stdin = StringIO()
        self.stdin_complete = 0
        self.data = StringIO()
        self.data_complete = 0

        # Output
        self.out = StringIO()
        self.err = StringIO()

        self.have_finished = 0

    def run(self):
        """Read records for this request and handle them through the
        request handler."""
        while 1:
            try:
                if self.conn.fileno() < 1:
                    # Connection lost
                    raise Exception("Connection lost")
            except:
                return

            select.select([self.conn], [], [])
            rec = Record()
            if rec.readRecord(self.conn):
                self._handle_record(rec)
            else:
                # EOF, connection closed. Break loop, end thread. 
                return

    def getFieldStorage(self):
        """Return a cgi FieldStorage constructed from the stdin and
        environ read from the server for this request."""
        self.stdin.reset()
        # cgi.FieldStorage will eat the input here...
        r = cgi.FieldStorage(fp=self.stdin, environ=self.env, keep_blank_values=1)
        # hence, we reset here so we can obtain
        # the data again...
        self.stdin.reset()
        return r

    def _flush(self, stream):
        """Flush a stream of this request."""
        stream.reset()

        rec = Record()
        rec.rec_type = FCGI_STDOUT
        rec.req_id = self.req_id
        data = stream.read()

        if not data:
            # Writing zero bytes would mean stream termination
            return

        while data:
            chunk, data = self.getNextChunk(data)
            rec.content = chunk
            rec.writeRecord(self.conn)
        # Truncate
        stream.reset()
        stream.truncate()

    def flush_out(self):
        """Flush Requests stdout stream."""
        self._flush(self.out)

    def flush_err(self):
        """Flush Requests stderr stream."""
        self._flush(self.err)

    def finish(self, status=0):
        """Finish this Request, flushing all output and
        possible exiting this thread."""
        if self.have_finished:
            return

        self.have_finished = 1

        # stderr
        if self.err.tell(): # just send err record if there is data on the err stream
            self.err.reset()
            rec = Record()
            rec.rec_type = FCGI_STDERR
            rec.req_id = self.req_id
            data = self.err.read()
            while data:
                chunk, data = self.getNextChunk(data)
                rec.content = chunk
                rec.writeRecord(self.conn)
            rec.content = ""
            rec.writeRecord(self.conn)      # Terminate stream

        # stdout
        self.out.reset()
        rec = Record()
        rec.rec_type = FCGI_STDOUT
        rec.req_id = self.req_id
        data = self.out.read()
        while data:
            chunk, data = self.getNextChunk(data)
            rec.content = chunk
            rec.writeRecord(self.conn)
        rec.content = ""
        rec.writeRecord(self.conn)      # Terminate stream

        # end request
        rec = Record()
        rec.rec_type = FCGI_END_REQUEST
        rec.req_id = self.req_id
        rec.appStatus = status
        rec.protocolStatus = FCGI_REQUEST_COMPLETE
        rec.writeRecord(self.conn)
        if not self.keep_conn:
            self.conn.close()
            if self.inthread:
                raise SystemExit

    #
    # Record handlers
    #
    def _handle_record(self, rec):
        """Handle record."""
        if rec.req_id == FCGI_NULL_REQUEST_ID:
            # Management record            
            self._handle_man_record(rec)
        else:
            # Application record
            self._handle_app_record(rec)

    def _handle_man_record(self, rec):
        """Handle management record."""
        rec_type = rec.rec_type
        if rec_type in KNOWN_MANAGEMENT_TYPES:
            self._handle_known_man_types(rec)
        else:
            # It's a management record of an unknown type. Signal the error.
            rec = Record()
            rec.rec_type = FCGI_UNKNOWN_TYPE
            rec.unknownType = rec_type
            rec.writeRecord(self.conn)

    def _handle_known_man_types(self, rec):
        """Handle a known management record."""
        if rec.rec_type == FCGI_GET_VALUES:
            reply_rec = Record()
            reply_rec.rec_type = FCGI_GET_VALUES_RESULT

            params = {'FCGI_MAX_CONNS': FCGI_MAX_CONNS,
                      'FCGI_MAX_REQS': FCGI_MAX_REQS,
                      'FCGI_MPXS_CONNS': FCGI_MPXS_CONNS,
                     }

            for name in rec.values:
                if name in params:
                    # We known this value, include in reply
                    reply_rec.values[name] = params[name]

            rec.writeRecord(self.conn)

    def _handle_app_record(self, rec):
        """Handle an application record. This calls the specified
        request_handler, if environ and stdin is complete."""
        if rec.rec_type == FCGI_BEGIN_REQUEST:
            # Discrete
            self._handle_begin_request(rec)
            return
        elif rec.req_id != self.req_id:
            log("Received unknown request ID %r" % rec.req_id)
            # Ignore requests that aren't active
            return
        if rec.rec_type == FCGI_ABORT_REQUEST:
            # Discrete
            rec.rec_type = FCGI_END_REQUEST
            rec.protocolStatus = FCGI_REQUEST_COMPLETE
            rec.appStatus = 0
            rec.writeRecord(self.conn)
            return
        elif rec.rec_type == FCGI_PARAMS:
            # Stream
            self._handle_params(rec)
        elif rec.rec_type == FCGI_STDIN:
            # Stream
            self._handle_stdin(rec)
        elif rec.rec_type == FCGI_DATA:
            # Stream
            self._handle_data(rec)
        else:
            # Should never happen. 
            log("Received unknown FCGI record type %r" % rec.rec_type)
            pass

        if self.env_complete and self.stdin_complete:
            # Call application request handler. 
            # The arguments sent to the request handler is:
            # self: us. 
            # req: The request.
            # env: The request environment
            # form: FieldStorage.
            self.req_handler(self, self.env, self.getFieldStorage())

    def _handle_begin_request(self, rec):
        """Handle begin request."""
        if rec.role != FCGI_RESPONDER:
            # Unknown role, signal error.
            rec.rec_type = FCGI_END_REQUEST
            rec.appStatus = 0
            rec.protocolStatus = FCGI_UNKNOWN_ROLE
            rec.writeRecord(self.conn)
            return

        self.req_id = rec.req_id
        self.keep_conn = rec.keep_conn

    def _handle_params(self, rec):
        """Handle environment."""
        if self.env_complete:
            # Should not happen
            log("Received FCGI_PARAMS more than once")
            return

        if not rec.content:
            self.env_complete = 1

        # Add all vars to our environment
        self.env.update(rec.values)

    def _handle_stdin(self, rec):
        """Handle stdin."""
        if self.stdin_complete:
            # Should not happen
            log("Received FCGI_STDIN more than once")
            return

        if not rec.content:
            self.stdin_complete = 1
            self.stdin.reset()
            return

        self.stdin.write(rec.content)

    def _handle_data(self, rec):
        """Handle data."""
        if self.data_complete:
            # Should not happen
            log("Received FCGI_DATA more than once")
            return

        if not rec.content:
            self.data_complete = 1

        self.data.write(rec.content)

    def getNextChunk(self, data):
        """Helper function which returns chunks of data."""
        chunk = data[:8192]
        data = data[8192:]
        return chunk, data

class FCGI:
    """FCGI requests"""

    def __init__(self, req_handler, fd=sys.stdin, port=None, max_requests=-1, backlog=5, max_threads=5):
        """Initialize main loop and set request_handler."""
        self.req_handler = req_handler
        self.fd = fd
        self.__port = port
        self._make_socket()
        # how many requests we have left before terminating this process, -1 means infinite lifetime:
        self.requests_left = max_requests
        # for socket.listen(backlog):
        self.backlog = backlog
        # how many threads we have at maximum (including the main program = 1. thread)
        self.max_threads = max_threads

    def accept_handler(self, conn, addr, inthread=False):
        """Construct Request and run() it."""
        self._check_good_addrs(addr)
        try:
            req = Request(conn, self.req_handler, inthread)
            req.run()
        except SocketErrorOnWrite:
            raise SystemExit

    def _make_socket(self):
        """Create socket and verify FCGI environment."""
        try:
            if self.__port:
                if isinstance(self.__port, str):
                    try:
                        os.unlink(self.__port)
                    except:
                        pass
                    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                    s.bind(self.__port)
                    # os.chmod(self.__port, 0660)
                else:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    # bind to the localhost
                    s.bind(('127.0.0.1', self.__port))
                s.listen(1)
            else:
                if hasattr(socket, 'fromfd'):
                    s = socket.fromfd(self.fd.fileno(), socket.AF_INET, socket.SOCK_STREAM)
                    s.getpeername()
                else: # we do not run on posix, fire up an FCGI external process
                    raise ValueError("FastCGI port is not setup correctly")
        except socket.error, (err, errmsg):
            if err != errno.ENOTCONN:
                raise RuntimeError("No FastCGI environment: %s - %s" % (repr(err), errmsg))

        self.sock = s

    def _check_good_addrs(self, addr):
        """Check if request is done from the right server."""
        # Apaches mod_fastcgi seems not to use FCGI_WEB_SERVER_ADDRS. 
        if 'FCGI_WEB_SERVER_ADDRS' in os.environ:
            good_addrs = os.environ['FCGI_WEB_SERVER_ADDRS'].split(',')
            good_addrs = [addr.strip() for addr in good_addrs] # Remove whitespace
        else:
            good_addrs = None

        # Check if the connection is from a legal address
        if good_addrs is not None and addr not in good_addrs:
            raise RuntimeError("Connection from invalid server!")

    def run(self):
        """Wait & serve. Calls request_handler on every request."""
        self.sock.listen(self.backlog)
        pid = os.getpid()
        log("Starting Process (PID=%d)" % pid)
        running = True
        while running:
            if not self.requests_left:
                # self.sock.shutdown(RDWR) here does NOT help with backlog
                log("Maximum number of processed requests reached, terminating this worker process (PID=%d)..." % pid)
                running = False
            elif self.requests_left > 0:
                self.requests_left -= 1
            if running:
                conn, addr = self.sock.accept()
                threadcount = _threading.activeCount()
                if threadcount < self.max_threads:
                    log("Accepted connection, %d active threads, starting worker thread..." % threadcount)
                    t = _threading.Thread(target=self.accept_handler, args=(conn, addr, True))
                    t.start()
                else:
                    log("Accepted connection, %d active threads, running in main thread..." % threadcount)
                    self.accept_handler(conn, addr, False)
        self.sock.close()
        log("Ending Process (PID=%d)" % pid)

