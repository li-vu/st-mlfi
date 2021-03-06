#!/usr/bin/env python
# -*- coding:utf-8 -*-
#=========================================================================
#     File: $Name: _parser_gen.py $
# Revision: $Rev: d41a1dc2 $
#  Created: $Date: 2014-05-27 12:10:07 $
# Modified: $Date: 2014-10-28 21:29:58 $
#   Author: $Author: Linh Vu Hong<lvho@dtu.dk> $
#-------------------------------------------------------------------------
# Description: Generate parser from a configuration file
#=========================================================================
import pprint
import re
from string import Template
import sys
sys.path.insert(0, "../..")
from mlfi.yply.yparser import YParser


class ParserCodeGenerator(object):

    def __init__(self, cfg_filename='annotparser_yacc.ypp'):
        """ Initialize the code generator from a configuration
            file.
        """
        self.cfg_filename = cfg_filename
        self.cfg_parser = YParser()
        self.tabsize = 4
        with open(cfg_filename, "r",encoding='utf8') as f:
            buf = f.read()
            self.cfg = self.cfg_parser.parse(buf,
                                             'parser_gen.y', debuglevel=0)

    def _gen_rule(self, rule, indent):
        cs = ["def p_%s(self,p):" % (rule.name)]
        cs.append('{0}""" {1} \n    {0}"""'.format(" " * self.tabsize, rule.prod))
        codelines = rule.code.splitlines()
        # a bit tweaking, ignore the first indent if all lines are 
        # indented with tabsize. This makes the config file more readable
        if all(i == "" or i.startswith(' '*self.tabsize) 
            for i in codelines):
            codelines = [i[self.tabsize:] if i else i 
                for i in codelines]
        if codelines and codelines[0] == "":
            codelines = codelines[1:]
        for c in codelines:
            cs.append("%s%s" % (" " * self.tabsize, c))
        cs = ["%s%s" % (" " * indent * self.tabsize, i) for i in cs]
        return "\n".join(cs)

    def generate(self, file=None):
        """ Generates the code into file, an open file buffer.
        """
        src = Template(_PROLOGUE_COMMENT).substitute(
            cfg_filename=self.cfg_filename)
        _precs = '\n'.join(
            ["%s%s," % (' ' * self.tabsize * 2, i) 
                                for i in self.cfg.precs])
        _opt_rules = '\n'.join(
            ["%s'%s'," % (' ' * self.tabsize * 3, i) 
                                for i in self.cfg.opt_rules])
        _list_rules = '\n'.join(
            ["%s'%s'," % (' ' * self.tabsize * 3, i)
                                for i in self.cfg.list_rules])
        _string_rules = '\n'.join(
            ["%s'%s'," % (' ' * self.tabsize * 3, i)
                                for i in self.cfg.string_rules])

        _productions = '\n\n'.join(
            [self._gen_rule(r, 1) for r in self.cfg.rules])

        src += Template(_PROLOGUE_CODE).substitute(
            start=self.cfg.start,
            precs=_precs,
            opt_rules=_opt_rules,
            list_rules=_list_rules,
            string_rules=_string_rules,
            productions=_productions)

        file.write(src)

_PROLOGUE_COMMENT = \
    r'''#!/usr/bin/env python
# -*- coding:utf-8 -*-
#-----------------------------------------------------------------
# ** ATTENTION **
# This code was automatically generated from the file:
# $cfg_filename
#
# Do not modify it directly. Modify the configuration file and
# run the generator again.
# ** ** *** ** **
#
# pymlannot: annotparser.py
#
# Copyright (C) 2014, Linh Vu Hong
#-----------------------------------------------------------------
'''

_PROLOGUE_CODE = r'''
import re
try:
    from .ply import yacc
    from .intervaltree import intervaltree
    from . import annotast as ast
    from .annotlexer import AnnotLexer
    from .plyparser import PLYParser, Coord, ParseError
except SystemError:
    from ply import yacc
    from intervaltree import intervaltree
    import annotast as ast
    from annotlexer import AnnotLexer
    from plyparser import PLYParser, Coord, ParseError
class AnnotParser(PLYParser):
    def __init__(
            self,
            lex_optimize=False,
            lextab='annotlextab',
            yacc_optimize=False,
            yacctab='annotyacctab',
            yacc_debug=False):
        """ Create a new pyAnnotparser.

            Some arguments for controlling the debug/optimization
            level of the parser are provided. The defaults are
            tuned for release/performance mode.
            The simple rules for using them are:
            *) When tweaking Annotparser/lexer, set these to False
            *) When releasing a stable parser, set to True

            lex_optimize:
                Set to False when you're modifying the lexer.
                Otherwise, changes in the lexer won't be used, if
                some lextab.py file exists.
                When releasing with a stable lexer, set to True
                to save the re-generation of the lexer table on
                each run.

            lextab:
                Points to the lex table that's used for optimized
                mode. Only if you're modifying the lexer and want
                some tests to avoid re-generating the table, make
                this point to a local lex table file (that's been
                earlier generated with lex_optimize=True)

            yacc_optimize:
                Set to False when you're modifying the parser.
                Otherwise, changes in the parser won't be used, if
                some parsetab.py file exists.
                When releasing with a stable parser, set to True
                to save the re-generation of the parser table on
                each run.

            yacctab:
                Points to the yacc table that's used for optimized
                mode. Only if you're modifying the parser, make
                this point to a local yacc table file

            yacc_debug:
                Generate a parser.out file that explains how yacc
                built the parsing table from the grammar.
        """
        self.lex = AnnotLexer(
            error_func=self._lex_error_func,
            on_scope_begin_func=self._lex_on_scope_begin_func,
            on_scope_end_func=self._lex_on_scope_end_func)

        self.lex.build(
            optimize=lex_optimize,
            lextab=lextab)
        self.tokens = self.lex.tokens

        rules_with_list = { 
$list_rules
        }

        for rule in rules_with_list:
            self._create_list_rule(rule)

        rules_with_string = { 
$string_rules
        }

        for rule in rules_with_string:
            self._create_list_rule(rule,"",'_string')

        rules_with_opt = {
$opt_rules
        }

        for rule in rules_with_opt:
            self._create_opt_rule(rule)

        self.parser = yacc.yacc(
            module=self,
            start='$start',
            debug=yacc_debug,
            optimize=yacc_optimize,
            tabmodule=yacctab)

        # Stack of scopes for keeping track of symbols. _scope_stack[-1] is
        # the current (topmost) scope. Each scope is a dictionary that
        # specifies whether a name is a type. If _scope_stack[n][name] is
        # True, 'name' is currently a type in the scope. If it's False,
        # 'name' is used in the scope but not as a type (for instance, if we
        # saw: int name;
        # If 'name' is not a key in _scope_stack[n] then 'name' was not defined
        # in this scope at all.
        self._scope_stack = [dict()]

        # Keeps track of the last token given to yacc (the lookahead token)
        self._last_yielded_token = None

    def parse(self, text, filename='', debuglevel=0):
        """ Parses code and returns an AST.

            text:
                A string containing the source code

            filename:
                Name of the file being parsed (for meaningful
                error messages)

            debuglevel:
                Debug level to yacc
        """
        self.lex.filename = filename
        self.lex.reset_lineno()
        self._scope_stack = [dict()]
        self._last_yielded_token = None
        return self.parser.parse(
                input=text,
                lexer=self.lex,
                debug=debuglevel)

    ######################--   PRIVATE   --######################

    def _push_scope(self):
        self._scope_stack.append(dict())

    def _pop_scope(self):
        assert len(self._scope_stack) > 1
        self._scope_stack.pop()
        
    def _add_typedef_name(self, name, coord):
        """ Add a new typedef name (ie a TYPEID) to the current scope
        """
        if not self._scope_stack[-1].get(name, True):
            self._parse_error(
                "Typedef %r previously declared as non-typedef "
                "in this scope" % name, coord)
        self._scope_stack[-1][name] = True

    def _add_identifier(self, name, coord):
        """ Add a new object, function, or enum member name (ie an ID) to the
            current scope
        """
        if self._scope_stack[-1].get(name, False):
            self._parse_error(
                "Non-typedef %r previously declared as typedef "
                "in this scope" % name, coord)
        self._scope_stack[-1][name] = False

    def _is_type_in_scope(self, name):
        """ Is *name* a typedef-name in the current scope?
        """
        for scope in reversed(self._scope_stack):
            # If name is an identifier in this scope it shadows typedefs in
            # higher scopes.
            in_scope = scope.get(name)
            if in_scope is not None: return in_scope
        return False

    def _lex_error_func(self, msg, line, column):
        self._parse_error(msg, self._coord(line, column))

    def _lex_on_scope_begin_func(self):
        self._push_scope()

    def _lex_on_scope_end_func(self):
        self._pop_scope()

    def _lex_type_lookup_func(self, name):
        """ Looks up types that were previously defined with
            typedef.
            Passed to the lexer for recognizing identifiers that
            are types.
        """
        is_type = self._is_type_in_scope(name)
        return is_type

    def _get_yacc_lookahead_token(self):
        """ We need access to yacc's lookahead token in certain cases.
            This is the last token yacc requested from the lexer, so we
            ask the lexer.
        """
        return self.lex.last_token

    ##
    ## Precedence and associativity of operators
    ##
    precedence = ( 
$precs
    )

    ##
    ## Grammar productions

$productions

    def p_empty(self, p):
        'empty : '
        p[0] = None

    def p_error(self, p):
        # If error recovery is added here in the future, make sure
        # _get_yacc_lookahead_token still works!
        #
        if p:
            self._parse_error(
                'before: %s' % p.value,
                self._coord(lineno=p.lineno,
                            column=self.lex.find_tok_column(p)))
        else:
            self._parse_error('At end of input', '')

if __name__ == "__main__":
    import pprint, sys
    from datetime import datetime

    t1 = datetime.now()
    parser = AnnotParser(lex_optimize=True, yacc_debug=False, yacc_optimize=True)
    print(datetime.now() - t1)

    buf = r"""
    "otc_unit_test_insts.mf" 19 455 461 "otc_unit_test_insts.mf" 19 455 466
    type(
      t Dynamic_gui.ItemPointer.ip_map_item list
    )
    ident(
      def ipmap "otc_unit_test_insts.mf" 25 586 588 "otc_unit_test_insts.mf" 49 1186 1189
    )
    "otc_unit_test_insts.mf" 21 497 503 "otc_unit_test_insts.mf" 21 497 508
    type(
      (t, int) Mlfi_type_path.field ->
      int Dynamic_gui.ItemPointer.field_k Dynamic_gui.ItemPointer.item_pointer ->
      t Dynamic_gui.ItemPointer.ip_map_item
    )
    ident(
      int_ref Dynamic_gui.ItemPointer.field "dynamic_gui_item_pointer.mf" 15 333 335 "dynamic_gui_item_pointer.mf" 15 333 417
    )
    """

    try:
        f = open('test.annot','r')
        buf = f.read()
    except:
        print("cannot read file")
    finally:
        f.close()

    # set debuglevel to 2 for debugging
    t = parser.parse(buf, 'x.annot', debuglevel=0)
    t.show(showcoord=False)
'''


if __name__ == "__main__":
    import sys
    ast_gen = ParserCodeGenerator('./annotparser_yacc.ypp')
    ast_gen.generate(open('../annotparser.py', 'w'))
