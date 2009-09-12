"""
    MoinMoin - Parsing of PHP session files

    @copyright: 2005 MoinMoin:AlexanderSchremmer (Thanks to Spreadshirt)
    @license: GNU GPL, see COPYING for details.
"""

#Known minor bugs/questions/ideas:
#How does object demarshalling work?
#The order of the python dictionaries is not stable compared to the PHP arrays
#The loader does not check the owner of the files, so be aware of faked session
#files.

import os
from MoinMoin import wikiutil

s_prefix = "sess_"
s_path = "/tmp"

class UnknownObject(object):
    """ Used in the return value if the input data could not be parsed. """
    def __init__(self, pos):
        self.pos = pos

    def __repr__(self):
        return "<Unknown object at pos %i>" % self.pos

def transformList(items):
    """ Transforms a list [1, 2, 3, 4, ...] into a
        [(1, 2), (3, 4), ...] generator. """
    for i in xrange(0, len(items), 2):
        yield (items[i], items[i+1])
    raise StopIteration

def parseValue(string, start=0):
    """ Parses the inner structure. """
    # TODO: replace "string" by something else
    #print "Parsing %r" % (string[start:], )

    val_type = string[start]
    try:
        header_end = string.index(':', 3+start)
        first_data = string[start+2:header_end]
    except ValueError:
        first_data = None

    #print "Saw type %r, first_data is %r." % (val_type, first_data)
    if val_type == 'a': # array (in Python rather a mixture of a list and a dict)
        i = 0
        items = []

        current_pos = header_end+2
        data = string
        while i != (int(first_data) * 2):
            item, current_pos = parseValue(data, current_pos)
            items.append(item)
            i += 1
            current_pos += 1

        t_list = list(transformList(items))
        try:
            result = dict(t_list) # note that dict does not retain the order
        except TypeError:
            result = list(t_list)
            #print "Warning, could not convert to dict: %r" %  (result, )
        return result, current_pos

    if val_type == 's': # string
        current_pos = header_end+2
        end = current_pos + int(first_data)
        data = string[current_pos:end]
        current_pos = end+1
        if data.startswith("a:"): #Sometimes, arrays are marshalled as strings.
            try:
                data = parseValue(data, 0)[0]
            except ValueError: #Hmm, wrongly guessed. Just an ordinary string
                pass
        return data, current_pos

    if val_type in ('i', 'b'): # integer or boolean
        current_pos = start+2
        str_buffer = ""
        while current_pos != len(string):
            cur_char = string[current_pos]
            if cur_char.isdigit() or cur_char == "-":
                str_buffer += cur_char
            else:
                cast = (val_type == 'i') and int or (lambda x: bool(int(x)))
                return cast(str_buffer), current_pos
            current_pos += 1

    if val_type == "N": # Null, called None in Python
        return None, start+1

    return UnknownObject(start), start+1

def parseSession(boxed):
    """ Parses the outer structure that is similar to a dict. """
    current_pos = 0
    session_dict = {}
    while current_pos < len(boxed):
        name_end = boxed.find("|", current_pos) # TODO: replace by .index()?
        name = boxed[current_pos:name_end]
        current_pos = name_end+1
        data, current_pos = parseValue(boxed, current_pos)
        current_pos += 1
        session_dict[name] = data

    return session_dict

def loadSession(key, path=s_path, prefix=s_prefix):
    """ Loads a particular session from the directory. The key needs to be the
        session id. """
    key = key.lower()
    filename = os.path.join(path, prefix + wikiutil.taintfilename(key))

    try:
        f = open(filename, "rb")
    except IOError, e:
        if e.errno == 2:
            return None # session does not exist
        else:
            raise

    blob = f.read()
    f.close()
    return parseSession(blob)

def listSessions(path=s_path, prefix=s_prefix):
    """ Lists all sessions in a particular directory. """
    return [os.path.basename(x).replace(s_prefix, '') for x in os.listdir(s_path)
            if x.startswith(s_prefix)]

if __name__ == '__main__':
    # testing code
    import time
    a = time.clock()

    #print s
    p_s = loadSession("...")
    import pprint
    pprint.pprint(p_s)
    print time.clock() - a
    print listSessions()

