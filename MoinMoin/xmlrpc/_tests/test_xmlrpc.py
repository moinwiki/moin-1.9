# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - tests for the xmlrpc module

    @copyright: 2007 by Karol Nowak <grywacz@gmail.com>
    @license: GNU GPL, see COPYING for details.
"""

from xmlrpclib import Fault

from MoinMoin.user import User
from MoinMoin.xmlrpc import XmlRpcBase


def test_fault_serialization(request):
    """test MoinMoin.xmlrpc.xmlrpc_system_multicall Fault serialization"""

    def xmlrpc_return_fault():
        return Fault(666, "Fault description")

    xmlrpc = XmlRpcBase(request)
    xmlrpc.xmlrpc_return_fault = xmlrpc_return_fault
    args = [{'methodName': 'return_fault', 'params': []}]

    print """If a XML RPC method returns a Fault, we should get a failure response
    instead of a serialized Fault, as it happened in the past. See revision
    8b7d6d70fc95 for details"""

    result = xmlrpc.xmlrpc_system_multicall(args)
    assert type(result[0]) is dict
    assert result[0].has_key("faultCode") and result[0].has_key("faultString")

def test_getAuthToken(request):
    """ Tests if getAuthToken passes without crashing """
    xmlrpc = XmlRpcBase(request)
    assert xmlrpc.xmlrpc_getAuthToken("Foo", "bar") == ""

coverage_modules = ['MoinMoin.xmlrpc']

