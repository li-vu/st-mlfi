#!/usr/bin/env python
# -*- coding:utf-8 -*-
#===============================================================================
#     File: $Name: yparser.py $
# Revision: $Rev: 9f3a7b71 $
#  Created: $Date: 2014-05-27 23:49:16 $
# Modified: $Date: 2014-06-29 02:04:10 $
#   Author: $Author: Linh Vu Hong<lvho@dtu.dk> $
#-------------------------------------------------------------------------------
# Description: parser for Unix yacc-based grammars
# 
# Tweaking from the original by:
# Author: David Beazley (dave@dabeaz.com)
# Date  : October 2, 2006
#===============================================================================

from .ylex import YLexer
from ..ply import *
from ._y_ast import *
from ..plyparser import PLYParser, Coord, ParseError


class YParser(PLYParser):
  def __init__(self):
    self.lex = YLexer(error_func=self._lex_error_func)
    self.lex.build()
    self.tokens = self.lex.tokens
    self._config = ParserConfig("",[],set(),set(),set(),[])
    rules_with_opt = [
        "defsection",
    ]

    for rule in rules_with_opt:
        self._create_opt_rule(rule)
    self.parser = yacc.yacc(module=self,
                            start='yacc',
                            debug=False,
                            tabmodule='yply.yacctab')

  def parse(self, text, filename='', debuglevel=0):
    """ Parses and returns an AST.

        text:
            A string containing the RSL source code

        filename:
            Name of the file being parsed (for meaningful
            error messages)

        debuglevel:
            Debug level to yacc
    """
    self.lex.filename = filename
    return self.parser.parse(
            input=text,
            lexer=self.lex,
            debug=debuglevel)

  ######################--   PRIVATE   --######################
  def _lex_error_func(self, msg, line, column):
      self._parse_error(msg, self._coord(line, column))

  def p_yacc(self,p):
      '''yacc : defsection_opt rulesection'''
      p[0] = self._config

  def p_defsection(self,p):
      '''defsection : definitions SECTION
                    | SECTION'''
      p.lexer.lastsection = 1

  def p_rulesection(self,p):
      '''rulesection : rules SECTION'''

  def p_definitions(self,p):
      '''definitions : definitions definition
                     | definition'''

  def p_definition_literal(self,p):
      '''definition : LITERAL'''

  def p_definition_start(self,p):
      '''definition : START ID'''
      self._config.start = p[2]

  def p_definition_token(self,p):
      '''definition : toktype opttype idlist optsemi '''
      if p[1] == '%left':
          self._config.precs.append(('left',) + tuple(p[3]))
      elif p[1] == '%right':
          self._config.precs.append(('right',) + tuple(p[3]))
      elif p[1] == '%nonassoc':
          self._config.precs.append(('nonassoc',)+ tuple(p[3]))

  def p_toktype(self,p):
      '''toktype : TOKEN
                 | LEFT
                 | RIGHT
                 | NONASSOC'''
      p[0] = p[1]

  def p_opttype(self,p):
      '''opttype : '<' ID '>'
                 | empty'''

  def p_idlist(self,p):
      '''idlist  : idlist optcomma tokenid
                 | tokenid'''
      if len(p) == 2:
          p[0] = [p[1]]
      else:
          p[0] = p[1]
          p[1].append(p[3])

  def p_tokenid(self,p):
      '''tokenid : ID 
                 | ID NUMBER
                 | QLITERAL
                 | QLITERAL NUMBER'''
      p[0] = p[1]
      
  def p_optsemi(self,p):
      '''optsemi : ';'
                 | empty'''

  def p_optcomma(self,p):
      '''optcomma : ','
                  | empty'''

  def p_definition_type(self,p):
      '''definition : TYPE '<' ID '>' namelist optsemi'''
      # type declarations are ignored

  def p_namelist(self,p):
      '''namelist : namelist optcomma ID
                  | ID'''

  def p_definition_union(self,p):
      '''definition : UNION CODE optsemi'''
      # Union declarations are ignored

  def p_rules(self,p):
      '''rules   : rules rule
                 | rule'''
      if len(p) == 2:
         rule = p[1]
      else:
         rule = p[2]

      # Print out a Python equivalent of this rule
      # Ignore embedded actions

      rulename = rule[0]
      rulecount = 1
      suffix = (len(rule[1]) > 1)
      for r in rule[1]:
          # r contains one of the rule possibilities
          name = "%s_%s" % (rulename,rulecount) if suffix else "%s" % (rulename)
          prod = []
          prodcode = ""
          for i in range(len(r)):
               item = r[i]
               if item[0] == '{':    # A code block
                  prodcode = item[1:-1]
                  break
               else:
                  prod.append(item)
          
          production = "%s : %s" % (rulename, " ".join(prod))
          self._config.rules.append(Rule(name,production,prodcode))
          rulecount += 1

  def p_rule(self,p):
     '''rule : ID ':' rulelist ';' '''
     p[0] = (p[1],[p[3]])

  def p_rule2(self,p):
     '''rule : ID ':' rulelist morerules ';' '''
     p[4].insert(0,p[3])
     p[0] = (p[1],p[4])

  def p_rule_empty(self,p):
     '''rule : ID ':' ';' '''
     p[0] = (p[1],[[]])

  def p_rule_empty2(self,p):
     '''rule : ID ':' morerules ';' '''
     
     p[3].insert(0,[])
     p[0] = (p[1],p[3])

  def p_morerules(self,p):
     '''morerules : morerules '|' rulelist
                  | '|' rulelist
                  | '|'  '''
   
     if len(p) == 2:   
         p[0] = [[]]
     elif len(p) == 3: 
         p[0] = [p[2]]
     else:
         p[0] = p[1]
         p[0].append(p[3])

  #   print "morerules", len(p), p[0]

  def p_rulelist(self,p):
     '''rulelist : rulelist ruleitem
                 | ruleitem'''

     if len(p) == 2:
          p[0] = [p[1]]
     else:
          p[0] = p[1]
          p[1].append(p[2])

  def p_ruleitem(self,p):
     '''ruleitem : CODE
                 | PREC
                 | QLITERAL
                 | ruleitem2'''
     p[0] = p[1]

  def p_ruleitem2(self,p):
     '''ruleitem2 : ID
                  | opt_ruleitem
                  | list_ruleitem
                  | string_ruleitem'''
     p[0] = p[1]

  def p_opt_ruleitem(self,p):
     ''' opt_ruleitem : '[' ruleitem2 ']'
     '''
     self._config.opt_rules.add(p[2])
     p[0] = p[2] + '_opt'

  def p_list_ruleitem(self,p):
     ''' list_ruleitem : '<' ruleitem2 '>'
     '''
     self._config.list_rules.add(p[2])
     p[0] = p[2] + '_list'

  def p_string_ruleitem(self,p):
     ''' string_ruleitem : '(' ruleitem2 ')'
     '''
     self._config.string_rules.add(p[2])
     p[0] = p[2] + '_string'

  def p_empty(self,p):
      '''empty : '''

  def p_error(self,p):
      pass
