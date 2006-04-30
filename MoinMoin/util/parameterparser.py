# -*- coding: iso-8859-1 -*-
"""
    MoinMoin macro parameter parser

    parses a given parameter string and seperates
    the single parameters and detects their type

    Possible parameterstypes are:

    Name      | short  | example
    ----------------------------
     Integer  | i      | -374
     Float    | f      | 234.234 23.345E-23
     String   | s      | 'Stri\'ng'
     Boolean  | b      | 0 1 True false
     Name     |        | case_sensitive | converted to string
    
    @copyright: 2004 by Florian Festi
    @license: GNU GPL, see COPYING for details.
"""

import re, types

class ParameterParser:

    def __init__(self, pattern):
        #parameter_re = "([^\"',]*(\"[^\"]*\"|'[^']*')?[^\"',]*)[,)]"
        name = "(?P<%s>[a-zA-Z_][a-zA-Z0-9_]*)"
        int_re = r"(?P<int>-?\d+)"
        float_re = r"(?P<float>-?\d+\.\d+([eE][+-]?\d+)?)"
        string_re = (r"(?P<string>('([^']|(\'))*?')|" +
                                r'("([^"]|(\"))*?"))')
        name_re = name % "name"
        name_param_re = name % "name_param"

        param_re = r"\s*(\s*%s\s*=\s*)?(%s|%s|%s|%s)\s*(,|$)" % (name_re,
                                                          float_re,
                                                          int_re,
                                                          string_re,
                                                          name_param_re)
        self.param_re = re.compile(param_re, re.U)
        self._parse_pattern(pattern)

    def _parse_pattern(self, pattern):
        param_re = r"(%(?P<name>\(.*?\))?(?P<type>[ifs]{1,3}))|\|"
        i = 0
        self.optional = -1
        named = False
        self.param_list = []
        self.param_dict = {}
        for match in re.finditer(param_re, pattern):
            if match.group() == "|":
                self.optional = i
                continue
            self.param_list.append(match.group('type'))
            if match.group('name'):
                named = True
                self.param_dict[match.group('name')[1:-1]] = i
            elif named:
                raise ValueError, "Named parameter expected"
            i += 1

    def __str__(self):
        return "%s, %s, optional:%s" % (self.param_list, self.param_dict,
                                        self.optional)

    def parse_parameters(self, input):
        """
        (4, 2)
        """

        parameter_list = [None] * len(self.param_list)
        parameter_dict = {}
        check_list = [0] * len(self.param_list)
            
        i = 0
        start = 0
        named = False
        while start<len(input):
            match = re.match(self.param_re, input[start:])
            if not match: raise ValueError, "Misformatted value"
            start += match.end()
            value = None
            if match.group("int"):
                value = int(match.group("int"))
                type = 'i'
            elif match.group("float"):
                value = float(match.group("float"))
                type = 'f'
            elif match.group("string"):
                value = match.group("string")[1:-1]
                type = 's'
            elif match.group("name_param"):
                value = match.group("name_param")
                type = 'n'
            else:
                value = None

            parameter_list.append(value)
            if match.group("name"):
                if not self.param_dict.has_key( match.group("name")):
                    raise ValueError, "Unknown parameter name '%s'" % match.group("name")
                nr = self.param_dict[match.group("name")]
                if check_list[nr]:
                    raise ValueError, "Parameter specified twice"
                else:
                    check_list[nr] = 1
                parameter_dict[match.group("name")] = value
                parameter_list[nr] = value
                named = True
            elif named:
                raise ValueError, "Only named parameters allowed"
            else:
                nr = i
                parameter_list[nr] = value
            # check type
            #if not type in self.param_list[nr]:

                
            i += 1
        return parameter_list, parameter_dict


    def _check_type(value, type, format):
        if type == 'n' and 's' in format: # n as s
            return value
        
        if type in format: return value # x -> x
        
        if type == 'i':
            if 'f' in format: return float(value) # i -> f
            elif 'b' in format: return value # i -> b
        elif type == 'f':
            if 'b' in format: return value  # f -> b
        elif type == 's':
            if 'b' in format:
                return value.lower() != 'false' # s-> b


        if 's' in format: # * -> s
            return str(value) 
        else:
            pass # XXX error


def main():
    pattern = "%i%sf%s%ifs%(a)s|%(b)s"
    param = ' 4,"DI\'NG", b=retry, a="DING"'

    #p_list, p_dict = parse_parameters(param)
    
    print 'Pattern :', pattern
    print 'Param :', param

    P = ParameterParser(pattern)
    print P
    print P.parse_parameters(param)


if __name__=="__main__":
    main()
