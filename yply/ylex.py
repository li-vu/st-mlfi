#!/usr/bin/env python
# -*- coding:utf-8 -*-
#===============================================================================
#     File: $Name: ylex.py $
# Revision: $Rev: f60361f0 $
#  Created: $Date: 2014-05-27 22:28:06 $
# Modified: $Date: 2014-05-28 12:32:17 $
#   Author: $Author: Linh Vu Hong<lvho@dtu.dk> $
#-------------------------------------------------------------------------------
# Description: Lexer for yacc grammar
# 
# Tweaking from the original by:
# Author: David Beazley (dave@dabeaz.com)
# Date  : October 2, 2006
#===============================================================================
import re
import sys

from ..ply import lex
from ..ply.lex import TOKEN


class YLexer(object):

    """ A lexer for the Yacc language. After building it, set the
    input text with input(), and call token() to get new
    tokens.

    The public attribute filename can be set to an initial
    filaneme, but the lexer will update it upon #line
    directives.
    """

    def __init__(self, error_func):
        """ Create a new Lexer.

        error_func:
        An error function. Will be called with an error
        message, line and column as arguments, in case of
        an error during lexing.
        """
        self.error_func = error_func
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

    tokens = (
        'LITERAL','SECTION','TOKEN','LEFT','RIGHT','PREC','START','TYPE','NONASSOC','UNION','CODE',
        'ID','QLITERAL','NUMBER'
    )

    states = (('code','exclusive'),)

    literals = [ ';', ',', '<', '>', '|',':', '[',']','(',')']
    t_ignore = ' \t'

    t_TOKEN     = r'%token'
    t_LEFT      = r'%left'
    t_RIGHT     = r'%right'
    t_NONASSOC  = r'%nonassoc'
    t_PREC      = r'%prec'
    t_START     = r'%start'
    t_TYPE      = r'%type'
    t_UNION     = r'%union'
    t_ID        = r'[a-zA-Z_][a-zA-Z_0-9]*'
    t_QLITERAL  = r'''(?P<quote>['"]).*?(?P=quote)'''
    t_NUMBER    = r'\d+'

    def t_SECTION(self,t):
        r'%%'
        if getattr(t.lexer,"lastsection",0):
             t.value = t.lexer.lexdata[t.lexpos+2:]
             t.lexer.lexpos = len(t.lexer.lexdata)
        else:
             t.lexer.lastsection = 0
        return t

    # Comments
    def t_ccomment(self,t):
        r'/\*(.|\n)*?\*/'
        t.lexer.lineno += t.value.count('\n')

    t_ignore_cppcomment = r'//.*'

    def t_LITERAL(self,t):
       r'%\{(.|\n)*?%\}'
       t.lexer.lineno += t.value.count("\n")
       return t

    def t_NEWLINE(self,t):
       r'\n'
       t.lexer.lineno += 1

    def t_code(self,t):
       r'\{'
       t.lexer.codestart = t.lexpos
       t.lexer.level = 1
       t.lexer.begin('code')

    def t_code_ignore_string(self,t):
        r'\"([^\\\n]|(\\.))*?\"'

    def t_code_ignore_char(self,t):
        r'\'([^\\\n]|(\\.))*?\''

    def t_code_ignore_comment(self,t):
       r'/\*(.|\n)*?\*/'

    def t_code_ignore_cppcom(self,t):
       r'//.*'

    def t_code_lbrace(self,t):
        r'\{'
        t.lexer.level += 1

    def t_code_rbrace(self,t):
        r'\}'
        t.lexer.level -= 1
        if t.lexer.level == 0:
             t.type = 'CODE'
             t.value = t.lexer.lexdata[t.lexer.codestart:t.lexpos+1]
             t.lexer.begin('INITIAL')
             t.lexer.lineno += t.value.count('\n')
             return t

    t_code_ignore_nonspace   = r'[^\s\}\'\"\{]+'
    t_code_ignore_whitespace = r'\s+'
    t_code_ignore = ""

    def t_code_error(self,t):
        raise RuntimeError

    def t_error(self,t):
        msg = 'Illegal character %s' % repr(t.value[0])
        self._error(msg, t)
        t.lexer.skip(1)

if __name__ == '__main__':
    def err_fun(msg, lc1, lc2):
        print("Lex error: {0}, {1}, {2}".format(msg, lc1, lc2))
    rlex = YLexer(error_func=err_fun)

    rlex.build(lextab='yacc.lextab')
    if len(sys.argv) > 1:
        f = open(sys.argv[1], "r")
        data = f.read()
        f.close()
    else:
        data = """
        primary_expr
        : prefix_expr {$$ = $1;}
        | infix_expr  {$$ = $1;}
        | dot_expr    {$$ = $1;}
        | disj_expr   {$$ = $1;}
        | conj_expr   {$$ = $1;}
        | sum_expr   {$$ = $1;}
        | prod_expr   {$$ = $1;}
        | sing_func_expr {$$ = $1;}
        | (sing_expr) {$$ = $1;}
        | val_func_expr {$$ = $1;}
        | isa_expr {$$ = $1;}
        | ite_expr {$$ = $1;}
        | case_expr {$$ = $1;}
        | let_expr {$$ = $1;}
        | set_func_expr {$$ = $1;}
        | membership_expr {$$ = $1;}
        | macro_call_expr {$$ = $1;}
        | INTEGER {$$ = new NExpr($1);}
        | '(' primary_expr ')' {$$ = $2;}
        ;
        """
        while 1:
            try:
                data += raw_input() + "\n"
            except:
                break

    rlex.input(data)

    # Tokenize
    while 1:
        tok = rlex.token()
        if not tok:
            break      # No more input
        print(tok)

            
            
           

        

