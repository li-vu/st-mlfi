#-----------------------------------------------------------------
# plyparser.py
#
# PLYParser class and other utilites for simplifying programming
# parsers with PLY
#
# Copyright (C) 2008-2012, Eli Bendersky
# License: BSD
#-----------------------------------------------------------------


class Coord(object):
    """ Coordinates of a syntactic element. Consists of:
            - File name
            - Line number
            - (optional) column number, for the Lexer
    """
    def __init__(self, file, line, column=None):
        self.file = file
        self.line = line
        self.column = column

    def __str__(self):
        str = "%s:%s" % (self.file, self.line)
        if self.column: str += ":%s" % self.column
        return str


class ParseError(Exception): pass


class PLYParser(object):
    def _create_opt_rule(self, rulename):
        """ Given a rule name, creates an optional ply.yacc rule
            for it. The name of the optional rule is
            <rulename>_opt
        """
        optname = rulename + '_opt'

        def optrule(self, p):
            p[0] = p[1]

        optrule.__doc__ = '%s : empty\n| %s' % (optname, rulename)
        optrule.__name__ = 'p_%s' % optname
        setattr(self.__class__, optrule.__name__, optrule)

    def _create_list_rule(self, rulename, delimiter='","',suffix='_list'):
        """ Given a rule name, creates an ply.yacc rule for a list.
            The name of the list-rule is <rulename>_list
        """
        listname = rulename + suffix

        def listrule_1(self, p):
            p[0] = [p[1]]

        listrule_1.__doc__ = '%s : %s' % (listname, rulename)
        listrule_1.__name__ = 'p_%s_1' % listname
        setattr(self.__class__, listrule_1.__name__, listrule_1)

        def listrule_2(self, p):
            idx = (2 if delimiter == "" else 3)
            p[0] = [p[1]] + p[idx]

        listrule_2.__doc__ = '%s : %s %s %s' % (listname, rulename, delimiter, listname)
        listrule_2.__name__ = 'p_%s_2' % listname
        setattr(self.__class__, listrule_2.__name__, listrule_2)

    def _coord(self, lineno, column=None):
        return Coord(
                file=self.lex.filename,
                line=lineno,
                column=column)

    def _parse_error(self, msg, coord):
        raise ParseError("%s: %s" % (coord, msg))
