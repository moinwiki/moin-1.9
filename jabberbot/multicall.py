""" XMLRPC MultiCall support for Python 2.3. Copied from xmlrpclib.py of Python 2.4.3. """

try:
    from xmlrpclib import MultiCall
except ImportError:
    from xmlrpclib import Fault

    class _MultiCallMethod:
        # some lesser magic to store calls made to a MultiCall object
        # for batch execution
        def __init__(self, call_list, name):
            self.__call_list = call_list
            self.__name = name
        def __getattr__(self, name):
            return _MultiCallMethod(self.__call_list, "%s.%s" % (self.__name, name))
        def __call__(self, *args):
            self.__call_list.append((self.__name, args))

    class MultiCallIterator:
        """Iterates over the results of a multicall. Exceptions are
        thrown in response to xmlrpc faults."""

        def __init__(self, results):
            self.results = results

        def __getitem__(self, i):
            item = self.results[i]
            if type(item) == type({}):
                raise Fault(item['faultCode'], item['faultString'])
            elif type(item) == type([]):
                return item[0]
            else:
                raise ValueError,\
                      "unexpected type in multicall result"

    class MultiCall:
        """server -> a object used to boxcar method calls

        server should be a ServerProxy object.

        Methods can be added to the MultiCall using normal
        method call syntax e.g.:

        multicall = MultiCall(server_proxy)
        multicall.add(2,3)
        multicall.get_address("Guido")

        To execute the multicall, call the MultiCall object e.g.:

        add_result, address = multicall()
        """

        def __init__(self, server):
            self.__server = server
            self.__call_list = []

        def __repr__(self):
            return "<MultiCall at %x>" % id(self)

        __str__ = __repr__

        def __getattr__(self, name):
            return _MultiCallMethod(self.__call_list, name)

        def __call__(self):
            marshalled_list = []
            for name, args in self.__call_list:
                marshalled_list.append({'methodName': name, 'params': args})

            return MultiCallIterator(self.__server.system.multicall(marshalled_list))
