"""Interface to directories and files, both in memory and on disk"""
from array import array
import weakref
import os, stat, struct

from StringIO import StringIO


DIRECTORIES = weakref.WeakValueDictionary()


def getDirectory(path, gen):
    dir = DIRECTORIES.get(path, None)

    if dir is None:
        dir = FSDirectory(path, gen)
        DIRECTORIES[path]=dir
    elif gen is True:
        dir.create()

    return dir

class FSDirectory:

    def __init__(self, path, gen):
        self.directory = path
        if gen is True:
            self.create()
        DIRECTORIES[path]=self

    def fpath(self, fname):
        return os.path.join(self.directory, fname)

    def create(self):
        path = self.directory
        if not os.path.exists(path):
            os.mkdir(path)
        try:
            files = os.listdir(path)
        except IOError:
            files = []
            
        for file in files:
            os.remove(os.path.join(path,file))

    def fileExists(self, name):
        return os.path.exists(self.fpath(name))

    def fileModified(self, name, path=None):
        return os.stat(self.fpath(name))[stat.ST_MTIME]
    
    def fileLength(self, name):
        return os.stat(self.fpath(name))[stat.ST_SIZE]
    
    def deleteFile(self, name):
        os.remove(self.fpath(name))

    def renameFile(self, frm, to):
        if os.path.exists(self.fpath(to)):
            os.remove(self.fpath(to))

        os.rename(self.fpath(frm),self.fpath(to))

    def createFile(self, name):
        #print "creating " + name
        f = FileStream(self.fpath(name), 'wb')
        f._name = name
        return f
    def openFile(self, name):
        #print "opening " + name
        f = FileStream(self.fpath(name), 'rb')
        f._name = name
        return f
    def close(self):
        pass
        #del(DIRECTORIES[self.directory])
        # breaks if object is used several times
        # and should not be needed as DIRECTORIES is a weakref dict

    def __str__(self):
        return 'FSDirectory:' + self.directory

class RAMDirectory:
    
    def __init__(self):
        self.files = {}

    
    def list(self):
        return self.files.keys()


    def fileExists(self, name):
        return (self.files.get(name, None) is not None)


    def fileModified(self, name):
        file = self.files[name]
        return file.lastModified
    

    def fileLength(self, name):
        file=self.files[name]
        return len(file)
    

    def deleteFile(self, name):
        del(self.files[name])


    def renameFile(self, name, newName):
        file = self.files[name]
        del(self.files[name])
        self.files[newName]=file


    def createFile(self, name):
        #print "creating RAM file " + name
        file = RAMStream()
        file._name = name
        self.files[name]=file
        return file


    def openFile(self, name):
        x = self.files[name]
        #print "opening RAM file " + name
        x.seek(0)
        return x
    
    def makeLock(self, name):
        """TBC"""


    def close(self):
        """Do nothing"""

class Stream(object):
    
    def writeByte(self, b):
        self.write(chr(b))

    def writeBytes(self, b, length):
        b[:length].tofile(self._getfile())

    def writeInt(self, i):        
        self.write(struct.pack("!I",i))

    def writeVInt(self, i):
        while (i & ~0x7F) != 0:
            self.writeByte((i & 0x7F) | 0x80)
            i = i >> 7
        self.writeByte(i)

    writeVLong = writeVInt
    
    def writeLong(self, i):
        self.writeInt((i >> 32) & 0xFFFFFFFF)
        self.writeInt(i & 0xFFFFFFFF)
        
    def writeString(self, s):
        length = len(s)
        self.writeVInt(length)
        #print "WRITING: %r" % s
        self.write(s.encode("utf8"))
                
    def getFilePointer(self):
        return self.tell()

    def readByte(self):
        return ord(self.read(1))

    def readBytes(self, b, offset, len):
        a = array('B')
        a.fromfile(self._getfile(), len)
        b[offset:offset+len] = a
        
    def readInt(self):
        return struct.unpack("!I",self.read(4))[0]
        

    def readVInt(self):
        b = self.readByte()
        i = b & 0x7F

        shift = 7
        while b & 0x80 != 0:
            b = self.readByte()
            i |= (b & 0x7F) << shift
            shift += 7
        return i


    def readLong(self):
        return(self.readInt() << 32 | (self.readInt() & 0xFFFFFFFFL))
    

    def readVLong(self):
        b = self.readByte()
        i = b & 0x7F

        shift = 7
        while b & 0x80 != 0:
            b = self.readByte()
            i |= (b & 0x7FL) << shift
            shift += 7

        return i
    

    def readString(self):
        length = self.readVInt()
        return self.readChars(length)
    
    def readChars(self, length): 
        buffer = []
        for i in range(length): 
            b = self.readByte() 
            if (b & 0x80) == 0: 
                buffer.append(unichr(b & 0x7F))
            elif (b & 0xE0) != 0xE0: 
                tmpInt = (((b & 0x1F) << 6)|(self.readByte() & 0x3F)) 
                buffer.append(unichr(tmpInt))
            else: 
                buffer.append(unichr((((b & 0x0f) << 12) |  
                             ((self.readByte() & 0x3F) << 6) | 
                             (self.readByte() & 0x3F))))
        x =  u''.join(buffer)
        #print "READING: %r" % x
        return x
        
class FileStream(Stream):

    def __init__(self, name, mode='rb', clone=0):
        if not clone:
            self.f = file(name, mode)
            self.length = os.stat(name).st_size
            self.isClone = 0
            self._position = 0
        else:
            self.f = name
            self.isClone = 1

    def close(self):
        pass
        #print "!!!@#! Closing " + self._name
        if not self.isClone:
            self.f.close()

    def seek(self, pos):
        self._position = pos
        self.f.seek(pos)

    def tell(self):
        return self._position

    def read(self, n):
        p = self.f.tell()
        if p != self._position:
            #print "!!!position mismatch in %s (at %s, wants to be at %s)" % (self._name, p, self._position)
            self.seek(self._position)
        s = self.f.read(n)
        self._position += len(s)
        return s
    

    def write(self, v):
        p = self.f.tell()
        if p != self._position:
            #print "!!!position mismatch in %s (at %s, wants to be at %s)" % (self._name, p, self._position)
            self.seek(self._position)
        self.f.write(v)
        self._position += len(v)
        

    def clone(self):
        g = FileStream(self.f, clone=1)
        g._name = self._name + " <clone>"
        g._position = self._position        
        return g

    def _getfile(self):
        return self.f
    
    def __getattr__(self, attr):
        return getattr(self.f, attr)

class RAMStream(Stream, StringIO):
    def __init__(self, *args):
        StringIO.__init__(self, *args)
        self.isClone = 0
        
    def close(self):
        pass
        
    def _getfile(self):
        return self

    def get_size(self):
        return len(self.getvalue())
    length = property(get_size)

    def clone(self):
        r = RAMStream(self.getvalue())
        r._name = self._name + " <clone>"
        r.isClone = 1
        r.seek(self.tell())
        return r
