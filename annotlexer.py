# #!/usr/bin/env python3
# # -*- coding:utf-8 -*-
# #===============================================================================
# #     File: $Name: Annotlexer.py $
# # Revision: $Rev: d41a1dc2 $
# #  Created: $Date: 2014-03-07 22:31:38 $
# # Modified: $Date: 2014-10-28 21:27:35 $
# #   Author: $Author: Linh Vu Hong<lvho@dtu.dk> $
# #-------------------------------------------------------------------------------
# # Description: a parser for dk-ixl generic model
# #===============================================================================
# import re
# import sys

import sys
import re
try:
    from .ply import lex
    from .ply.lex import TOKEN
except SystemError:
    from ply import lex
    from ply.lex import TOKEN

class AnnotLexer(object):

    """ A lexer for the language specifying mlfi annotation files. 
    After building it, set the input text with input(), and call 
    token() to get new tokens.

    The public attribute filename can be set to an initial
    filaneme, but the lexer will update it upon #line
    directives.
    """

    def __init__(self, error_func, on_scope_begin_func, on_scope_end_func):
        """ Create a new Lexer.

        error_func:
        An error function. Will be called with an error
        message, line and column as arguments, in case of
        an error during lexing.

        on_scope_begin_func, on_scope_end_func:
        Called when a SCOPE is encountered
        """
        self.error_func = error_func
        self.on_scope_begin_func = on_scope_begin_func
        self.on_scope_end_func = on_scope_end_func
        self.filename = ''

        # Keeps track of the last token returned from self.token()
        self.last_token = None

        # Allow either "# line" or "# <num>" to support GCC's
        # cpp output
        #
        self.line_pattern = re.compile('([ \t]*line\W)|([ \t]*\d+)')

    def build(self, **kwargs):
        """ Builds the lexer from the specification. Must be
        called after the lexer object is created.

        This method exists separately, because the PLY
        manual warns against calling lex.lex inside
        __init__
        """
        self.lexer = lex.lex(object=self, **kwargs)

    def reset_lineno(self):
        """ Resets the internal line number counter of the lexer.
        """
        self.lexer.lineno = 1

    def input(self, text):
        self.lexer.input(text)

    def token(self):
        self.last_token = self.lexer.token()
        return self.last_token

    def find_tok_column(self, token):
        """ Find the column of the token in its line.
        """
        last_cr = self.lexer.lexdata.rfind('\n', 0, token.lexpos)
        return token.lexpos - last_cr

    # --   PRIVATE   --######################

    #
    # Internal auxiliary methods
    #
    
    def _error(self, msg, token):
        location = self._make_tok_location(token)
        self.error_func(msg, location[0], location[1])
        self.lexer.skip(1)

    def _make_tok_location(self, token):
        return (token.lineno, self.find_tok_column(token))

    #
    # Reserved keywords
    #
    keywords = ( "TYPE", "IDENT", "CALL")

    keyword_map = {}
    for keyword in keywords:
        keyword_map[keyword.lower()] = keyword

    #
    # All the tokens recognized by the lexer
    #
    tokens = (
    'FILENAME',
    'NUMBER',
    'VAL'
    # operators
    ) + keywords

    # literals
    # literals = [] #['(', ')']

    #
    # Regexes for use in tokens
    #
    #
    t_NUMBER  = r'[0-9]+'

    identifier = r'[a-zA-Z_][0-9a-zA-Z_]*'
    @TOKEN(identifier)
    def t_ID(self, t):
        if t.value in self.keyword_map:
            t.type = self.keyword_map[t.value]
        return t

    def t_FILENAME(self,t):
        r'"[a-zA-Z_][0-9a-zA-Z_]*\.mf[i]?"'
        return t

    def t_VAL(self, t):
        r"\(\n\s+(.|\n)+?\n\)"
        t.lexer.lineno += t.value.count('\n')
        t.value = t.value.strip('(').strip(')').strip()
        return t

    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)

    # A string containing ignored characters (spaces and tabs).
    t_ignore = ' \t'

    # Error handling rule
    def t_error(self, t):
        msg = 'Illegal character %s' % repr(t.value[0])
        self._error(msg, t)

if __name__ == "__main__":
    def nothing(*args):
        pass

    def err_fun(msg, lc1, lc2):
        print("Lex error: {0}, {1}, {2}".format(msg, lc1, lc2))

    lx = AnnotLexer(error_func=err_fun,
                    on_scope_begin_func=nothing,
                    on_scope_end_func=nothing)
    lx.build(optimize=True,
                    lextab='annot.lextab')
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

    lx.input(buf)
    while 1:
        tok = lx.token()
        if not tok:
            break      # No more input
        print(tok)