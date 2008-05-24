import ply.lex as lex
import ply.yacc as yacc

import sys, re

import munge.ccg.nodes as ccg
from munge.cats.cat_defs import C
from munge.util.err_utils import warn, err

tokens = ("SLASH", "ATOM", "OP", "LPAREN", "RPAREN", "REGEX")

t_REGEX = r'/([^/]|\/)+/'
# This is pretty hacky. We rely on the fact that / or \ are never valid categories
# and neither are [/\]X or X[/\] for any X, letting us distinguish between a valid
# category and a regex.
t_ATOM = r'[^/][\w\d_\[\]()/\\]+[^/]|[\w\d_\[\]()]{2}|[\w\d_\[\]()]'

t_ignore = ' \t\r\v\f\n'
    
t_OP = r'!?((<-?\d?)|<<,?|>>\'?|\.\.?|\$\.?\.?)'
t_LPAREN = r'\{'
t_RPAREN = r'\}'

def t_error(t):
    warn("Illegal character `%s' encountered.", t.value[0])
    t.lexer.skip(1)
    
def p_error(stk):
    err("Syntax error encountered.")

class Node(object):
    def __init__(self, anchor, constraints=None):
        self.anchor = anchor
        
        if not constraints: constraints = []
        self.constraints = constraints
        
    def __repr__(self):
        return "%s%s%s" % (self.anchor, ' ' if self.constraints else '', ' '.join(str(c) for c in self.constraints))
        
    def is_satisfied_by(self, node):
        if self.anchor.is_satisfied_by(node):
            return all(constraint.is_satisfied_by(node) for constraint in self.constraints)
        return False
        
class Constraint(object):
    def __init__(self, operator, rhs):
        self.operator = operator
        self.rhs = rhs
    def __repr__(self):
        return "%s %s" % (self.operator, self.rhs)
    def is_satisfied_by(self, node):
        if self.operator == '<':
            return self.rhs.is_satisfied_by(node.lch) or \
                   self.rhs.is_satisfied_by(node.rch)
        return False
        
class Group(object):
    def __init__(self, node):
        self.node = node
    def __repr__(self):
        return "{%s}" % self.node
    def is_satisfied_by(self, node):
        return self.node.is_satisfied_by(node)

class Atom(object):
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return self.value
    def is_satisfied_by(self, node):
        return self.value == str(node.cat)
        
class RE(object):
    def __init__(self, source):
        self.source = source
        self.regex = re.compile(source)
    def __repr__(self):
        return "/%s/" % self.source
    def is_satisfied_by(self, node):
        return self.regex.match(str(node.cat)) is not None
        
def p_node(stk):
    '''
    node : matcher
         | node constraint_list
         | group
    '''
    if len(stk) == 2:
        stk[0] = Node(stk[1])
    elif len(stk) == 3:
        stk[0] = Node(stk[1])
        stk[0].constraints.extend(stk[2])
    elif len(stk) == 4:
        stk[0] = stk[1]
            
def p_constraint_list(stk):
    '''
    constraint_list : constraint constraint_list
                    | constraint
    '''
    if len(stk) == 3:
        stk[0] = [stk[1]] + stk[2]
    elif len(stk) == 2:
        stk[0] = [stk[1]]
        
def p_constraint(stk):
    '''
    constraint : OP matcher
               | OP LPAREN node RPAREN
    '''
    if len(stk) == 3:
        stk[0] = Constraint(stk[1], stk[2])
    elif len(stk) == 5:
        stk[0] = Constraint(stk[1], Group(stk[3]))
        
def p_group(stk):
    '''
    group : LPAREN node RPAREN
    '''
    stk[0] = Group(stk[2])
    
def p_matcher(stk):
    '''
    matcher : atom 
            | regex
    '''
    stk[0] = stk[1]
    
def p_atom(stk):
    '''
    atom : ATOM
    '''
    stk[0] = Atom(stk[1])

def p_regex(stk):
    '''
    regex : REGEX
    '''
    stk[0] = RE(stk[1][1:-1])

if __name__ == '__main__':
    # lex.lex()
    # lex.input(sys.argv[1])
    # 
    # for tok in iter(lex.token, None):
    #     print "%s %s" % (tok.type, tok.value)
    lex.lex(debug=1)
    l=sys.argv[1]
    lex.input(l)
    for tok in iter(lex.token, None):
        print tok.type, tok.value
    yacc.yacc()

    p = yacc.parse(sys.argv[1])
    print p
    print type(p.anchor)
    t = ccg.Node(
            C('A'), 0,0, None, 
            ccg.Node(
                C('B'), 0, 0, None,
                ccg.Leaf(C('C'), 'pos', 'pos', 'C', 'C'), None
                ),
            ccg.Leaf(
                C('C'), 'pos', 'pos', 'D', 'D'
                )
            )
    print t
    print p.is_satisfied_by(t)
