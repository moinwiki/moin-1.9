# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.xmlrpc.xmlrpc_system_multicall Fault serialization

    @copyright: 2007 by Karol Nowak <grywacz@gmail.com>
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.xmlrpc import XmlRpcBase
from MoinMoin.request.request_cli import Request
from xmlrpclib import Fault

def xmlrpc_return_fault():
    return Fault(666, "Fault description")

def test_fault_serialization():
    xmlrpc = XmlRpcBase(Request())
    xmlrpc.xmlrpc_return_fault = xmlrpc_return_fault
    args = [{'methodName': 'return_fault', 'params': []}]

    print """If a XML RPC method returns a Fault, we should get a failure response
    instead of a serialized Fault, as it happened in the past. See revision
    8b7d6d70fc95 for details"""

    result = xmlrpc.xmlrpc_system_multicall(args)
    assert(type(result[0]) == dict)
    assert(result[0].has_key("faultCode") and result[0].has_key("faultString"))

