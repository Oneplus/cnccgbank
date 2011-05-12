import sys, copy

from apps.util.config import config
config.set(show_vars=True, curly_vars=True)

from munge.cats.headed.parse import *
from munge.cats.cat_defs import S, Sdcl, NP, N
from munge.util.err_utils import *
from munge.trees.traverse import leaves

from apps.util.echo import echo

def variables():
    '''Returns an iterator over variable names. The first variable name returned is _,
for the outermost variable.'''
    return iter('_YZWVUTRQABCDEF')

def is_modifier(cat):
    '''Returns whether _cat_ is of the form X/X.'''
    return cat.left.equal_respecting_features(cat.right) and cat.left.slot.var is cat.right.slot.var

def is_np_n(cat):
    '''Returns whether _cat_ is the category NP/N.'''
    return cat.left == NP and cat.right == N
    
C = parse_category
Exceptions = (
    (C(r'(N/N)\(S[dcl]\NP)'), C(r'((N{Z}/N{Z}){_}\(S[dcl]{Y}\NP{Z}){Y}){_}')),
    (C(r'(N/N)\(S[dcl]/NP)'), C(r'((N{Z}/N{Z}){_}\(S[dcl]{Y}/NP{Z}){Y}){_}')),
    (C(r'(S[dcl]\NP)/(S[dcl]\NP)'), C(r'((S[dcl]{_}\NP{Y}){_}/(S[dcl]{Z}\NP{Y}){Z}){_}')),
    # gapped long bei
    (C(r'((S[dcl]\NP)/((S[dcl]\NP)/NP))/NP'), C(r'(((S[dcl]{_}\NP{Y}){_}/((S[dcl]{Z}\NP{W}){Z}/NP{Y}){Z}){_}/NP{W}){_}')),
    # non-gapped long bei
    (C(r'((S[dcl]\NP)/(S[dcl]\NP))/NP'), C(r'(((S[dcl]{_}\NP{W}){_}/(S[dcl]{Z}\NP{Y}){Z}){_}/NP{Y}){_}')),
    # gapped short bei
    (C(r'(S[dcl]\NP)/((S[dcl]\NP)/NP)'), C(r'((S[dcl]{_}\NP{Y}){_}/((S[dcl]{W}\NP{Z}){W}/NP{Y}){W}){_}')),
    # non-gapped short bei
    # TODO: coincides with the above control/raising category
#    (C(r'(S[dcl]\NP)/(S[dcl]\NP)'), C(r'((S[dcl]{_}\NP){_}/(S[dcl]\NP)){_}')),

    # hacks
    # not a modifier category:
    (C(r'((S[dcl]\NP)/(S[dcl]\NP))/((S[dcl]\NP)/(S[dcl]\NP))'),
     C(r'(((S[dcl]{Y}\NP{Z}){Y}/(S[dcl]{W}\NP{Z}){W}){Y}/((S[dcl]{Y}\NP{Z}){Y}/(S[dcl]{W}\NP{Z}){W}){W}){_}')),
     
    (C(r'((S[dcl]\NP)/NP)/((S[dcl]\NP)/NP)'),
     C(r'(((S[dcl]{Y}\NP{Z}){Y}/NP{W}){Y}/((S[dcl]{Y}\NP{Z}){Y}/NP{W}){Y}){_}')),
     
    #(C(r'((S[dcl]\NP)/((S[dcl]\NP)/NP))/NP'),
    # C(r'(((S[dcl]{_}\NP{Y}){_}/((S[dcl]{Z}\NP{W}){Z}/NP{Y}){Z}){_}/NP{W}){_}')),
     
    # make sure things which look like modifier categories but aren't are given the right markedup
    (C(r'(S[dcl]\S[dcl])/NP'), C(r'((S[dcl]{_}\S[dcl]{Z}){_}/NP{Y}){_}')),
    (C(r'(S\S)\(S\S)'), C(r'((S{Y}\S{Z}){Y}\(S{Y}\S{Z}){Y}){_}')),
    (C(r'(S\S)/(S\S)'), C(r'((S{Y}\S{Z}){Y}/(S{Y}\S{Z}){Y}){_}')),
    (C(r'(S[dcl]\S[dcl])/S[dcl]'), C(r'((S[dcl]{_}\S[dcl]{Z}){_}/S[dcl]{Y}){_}')),
    
    (C(r'((S\S)/(S\NP))/NP'), C(r'(((S{Y}\S{Z}){Y}/(S{W}\NP{V}){W}){_}/NP{Y}){_}')),

    (C(r'S[q]\S[dcl]'), C(r'(S[q]{Y}\S[dcl]{Y}){_}')),

    # short bei for bei VPdcl/VPdcl (wo bei qiangzhi)
    (C(r'(S[dcl]\NP)/(((S[dcl]\NP)/(S[dcl]\NP))/NP)'), C(r'((S[dcl]{_}\NP{Y}){_}/(((S[dcl]{Z}\NP{Y}){Z}/(S[dcl]{W}\NP{Y}){W}){Z}/NP{Y}){Z}){_}')),

    # long bei for bei NP VPdcl/VPdcl (wo bei ta qiangzhi)
    (C(r'((S[dcl]\NP)/(((S[dcl]\NP)/(S[dcl]\NP))/NP))/NP'),
     C(r'(((S[dcl]{_}\NP{Y}){_}/(((S[dcl]{V}\NP{Z}){V}/(S[dcl]{W}\NP{Y}){W}){V}/NP{Y}){V}){_}/NP{Z}){_}')),
      #C(r'(((S[dcl]{_}\NP{Y}){_}/(((S[dcl]{W}\NP{Z}){W}/(S[dcl]{V}\NP{Y}){V}){W}/NP{Y}){W}){_}/NP{Z}){_}')),
    
    # VPdcl/VPdcl modifier category fix
    (C(r'(((S[dcl]\NP)/(S[dcl]\NP))/NP)/(((S[dcl]\NP)/(S[dcl]\NP))/NP)'), 
     C(r'((((S[dcl]{Z}\NP{Y}){Z}/(S[dcl]{W}\NP{Y}){W}){Z}/NP{Y}){V}/(((S[dcl]{Z}\NP{Y}){Z}/(S[dcl]{W}\NP{Y}){W}){Z}/NP{Y}){V}){_}')),
    
    # gei category fix (NP gei NP NP VP e.g. tamen gei haizi jihui xuanze)
    (C(r'(((S[dcl]\NP)/(S[dcl]\NP))/NP)/NP'),
     C(r'((((S[dcl]{_}\NP{W}){_}/(S[dcl]{W}\NP{Y}){W}){_}/NP{Z}){_}/NP{Y}){_}')),

    # this category is probably not correct
    (C(r'((S[dcl]\NP)/(S[dcl]\NP))/S[dcl]'),
     C(r'(((S[dcl]{_}\NP{V}){_}/(S[dcl]{W}\NP{Z}){W}){_}/S[dcl]{Y}){_}')),
    
    # nor this (20:31(7))
    (C(r'((S[dcl]\NP)/(S[dcl]\NP))/PP'),
     C(r'(((S[dcl]{_}\NP{Y}){_}/(S[dcl]{W}\NP{Z}){W}){_}/PP{V}){_}')),

)

def get_cached_category_for(cat, lex):
    '''If _cat_ matches one of the mappings defined in Exceptions, returns a copy of
the cached category, filling in its outermost variable's lex with _lex_.'''
    for frm, to in Exceptions:
        if cat.equal_respecting_features(frm):
            result = copy.deepcopy(to)
#            result.slot.head.lex = lex
            return result
    return None

n = 1
def label(cat, vars=None, lex=None):
    '''Labels the category _cat_ using the markedup labelling algorithm, with
available variable labels _vars_ and lexical item _lex_.'''
    global n
    cached = get_cached_category_for(cat, lex)
    if cached: 
        cp = copy.deepcopy(cached)
#        cp.slot.head.lex = cat.slot.head.lex
        return cp
        
    available = vars or variables()

    if cat.slot.var == "?":
        suffix = str(n) if config.debug_vars else ''
        cat.slot.var = (available.next() + suffix)

    if cat.is_complex():
        c = cat
        while c.is_complex() and not (is_modifier(c) or is_np_n(c)):
            c.left.slot = cat.slot
            c = c.left

        if is_modifier(cat):
            cat._left = label(cat.left, available, lex)
            cat._right = copy.copy(cat._left)

        elif is_np_n(cat):
            cat._left = label(cat.left, available, lex)
            cat._right.slot = cat._left.slot

        else:
            cat._left = label(cat.left, available, lex)
            cat._right = label(cat.right, available, lex)

    n += 1
    return cat

PREFACE = "# this file was generated by the following command(s):"
def write_markedup(cats, file):
    print >>file, PREFACE
    print >>file
    
    for cat in cats:
        print >>file, cat.__repr__(suppress_vars=True)
        print >>file, "\t", 0, cat.__repr__()
        print >>file

def naive_label_derivation(root):
    '''Applies the markedup labelling algorithm to each leaf under _root_.'''
    for leaf in leaves(root):
#        print "%s ->" % leaf.cat,
        leaf.cat = label(leaf.cat, lex=leaf.lex)
        leaf.cat.slot.head.lex = leaf.lex
#        print "%s" % leaf.cat
        
    return root

if __name__ == '__main__':
    # for cat in cats:
    #     print label(cat)

    import sys
    write_markedup(map(label, map(parse_category, sys.stdin.xreadlines())), sys.stdout)
    # 
    # print label(parse_category(r'((S\NP)/(S\NP))/NP'))
    # print label(parse_category(r'(S\NP)/(S\NP)'))
    # print label(parse_category(r'(S[dcl]\NP)/NP'))
    # print label(parse_category(r'((S[dcl]\NP)/NP)/PP'))
    # print label(parse_category(r'(((S[dcl]\NP)/NP)/NP)/PP'))
    # print label(parse_category(r'(S[dcl]\NP)/(S[dcl]\NP)'))
    # print label(parse_category(r'N/N'))
    # print label(parse_category(r'(N/N)/(N/N)'))
    # print label(parse_category(r'((N/N)/(N/N))/((N/N)/(N/N))'))
    # print label(parse_category(r'PP/LCP'))
    # print label(parse_category(r'NP'))
    # print label(parse_category(r'(N/N)\NP'))
    # print label(parse_category(r'(NP\NP)/(S[dcl]\NP)'))
    # print label(parse_category(r'NP/N'))
    # print label(parse_category(r'(N/N)\(S[dcl]/NP)'))
