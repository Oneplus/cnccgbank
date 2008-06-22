from munge.cats.parse import parse_category
from munge.cats.nodes import APPLY, COMP, NULL, ALL, BACKWARD, FORWARD
from munge.cats.cat_defs import *

def analyse(l, r, cur, examine_modes=False):
    '''Determines which parser rule was used in the production [l r -> cur].'''
    return (try_unary_rules(l, r, cur) if not r else
            try_application(l, r, cur, examine_modes) or
            try_absorption(l, r, cur) or
            try_composition_or_substitution(l, r, cur, examine_modes))

def try_unary_rules(l, r, cur):
    '''Determines if [l r -> cur] matches any unary rules.'''
    if l == SbNP:
        for cand_cat, rule in {
            SfS: "lex_typechange",
            NP:  "lex_typechange",
            SbNPfSbNP: "lex_typechange",
            SbS: "lex_typechange"
        }.iteritems(): 
            if cur == cand_cat: return rule

    if l == SfNP and cur == NPbNP:
        return "lex_typechange"

    if cur.is_complex():
        if cur.right.is_complex(): # Type raising
            if cur.right.right == l:
                if cur.direction == FORWARD and cur.right.direction == BACKWARD:
                    return "fwd_raise"
                elif cur.direction == BACKWARD and cur.right.direction == FORWARD:
                    return "bwd_raise"

        if l.is_complex(): # Other special unary rules
            if l == SbNP:
                if cur == NPbNP or cur == NbN:
                    return "appositive_typechange"
                if cur == SbNPbSbNP:
                    return "clause_mod_typechange"

    elif not l.is_complex(): # Atomic -> atomic rules
        if str(l.cat) == 'N' and str(cur.cat) == 'NP': return "np_typechange"

    return None # no rule matched

def allows_application(mode_index):
    '''Returns whether the given mode indicated by the index allows the
application combinatory rules.'''
    return mode_index in (APPLY, COMP, ALL)

def is_application(appl, arg, result, examine_modes=False):
    '''Returns whether [appl arg -> result] is an instance of one of the
two application combinatory rules.'''
    return ((not examine_modes) or allows_appl(appl.mode)) and \
            appl.right == arg and appl.left == result 

def try_application(l, r, cur, examine_modes=False):
    '''Determines if [l r -> cur] matches any application rules. If _examine_modes_ is
    true, then the modes of the arguments are checked to see if they permit application.'''
    if l.is_complex() and is_application(l, r, cur, examine_modes):
        if l.direction == FORWARD: return "fwd_appl"
    elif r.is_complex() and is_application(r, l, cur, examine_modes):
        if r.direction == BACKWARD: return "bwd_appl"

    return None

def allows_composition(mode_index):
    '''Returns whether the given mode indicated by the index allows the
composition combinatory rules.'''
    return mode_index in (COMP, ALL)

def is_composition(l, r, result, examine_modes=False):
    '''Returns whether [appl arg -> result] is an instance of one of 
the four composition combinatory rules.'''
    return ((not examine_modes) or (allows_composition(l.mode) and allows_composition(r.mode))) and \
            l.right == r.left and l.left == result.left and r.right == result.right

def try_composition(l, r, cur, examine_modes=False):
    '''Determines if [l r -> cur] matches any composition rules. If _examine_modes_ is
    true, then the modes of the arguments are checked to see if they permit composition.'''
    if is_composition(l, r, cur, examine_modes):
        if l.direction == FORWARD: # Forward harmonic or crossed composition
            if cur.direction == FORWARD and cur.direction == r.direction:
                return "fwd_comp"
            if cur.direction == BACKWARD and cur.direction != r.direction:
                return "fwd_xcomp"

    if is_composition(r, l, cur, examine_modes):
        if r.direction == BACKWARD: # Backward harmonic or crossed composition
            if cur.direction == FORWARD and cur.direction != r.direction:
                return "bwd_xcomp"
            if cur.direction == BACKWARD and cur.direction == r.direction:
                return "bwd_comp"

    # Recognise backward recursive crossed composition with depth 1 as a special case
    # (Y / a) /Z   X \ Y ->  (X   / a)/Z
    #  |__ | _ | _ | __|      |   |    |
    #      |   |__ | ________ | _ |____|
    #      |       |__________|   |
    #      | _____________________|
    if l.left.is_complex() and cur.left.is_complex() and \
       l.left.left == r.right and l.right == cur.right and \
       r.left == cur.left.left and l.right == cur.right:
        return "bwd_r1xcomp"

    return None

def is_substitution(l, r, cur, examine_modes=False):
    '''Returns whether [appl arg -> result] is an instance of one of 
the four substitution combinatory rules.'''
    return ((not examine_modes) or (allows_comp(lhs.mode) and allows_comp(rhs.mode))) and \
            l.left.left == cur.left and l.left.right == r.left and \
            l.right == r.right and r.right == cur.right

def try_substitution(l, r, cur, examine_modes=False):
    '''Determines if [l r -> cur] matches any substitution rules. If _examine_modes_ is
    true, then the modes of the arguments are checked to see if they permit substitution.'''
    if l.left.is_complex():
        if is_substitution(l, r, cur, examine_modes) and \
           l.left.direction == FORWARD:
            if l.direction == FORWARD and \
               r.direction == FORWARD and \
               cur.direction == FORWARD:
                return "fwd_subst"
            elif l.direction == BACKWARD and \
                 r.direction == BACKWARD and \
                 cur.direction == BACKWARD:
                return "fwd_xsubst"
    elif r.left.is_complex():
        if is_substitution(r, l, cur, examine_modes) and \
           r.left.direction == BACKWARD:
            if r.direction == FORWARD and \
               l.direction == FORWARD and \
               cur.direction == FORWARD:
                return "bwd_xsubst"
            elif r.direction == BACKWARD and \
                 l.direction == BACKWARD and \
                 cur.direction == BACKWARD:
                return "bwd_subst"

    return None

def try_composition_or_substitution(l, r, cur, examine_modes=False):
    '''Determines whether [l r -> cur] matches any composition or substitution rules. Both of these
require that all of l, r, cur be compound categories.'''
    if l.is_complex() and r.is_complex() and cur.is_complex():
        return try_composition(l, r, cur, examine_modes) or \
               try_substitution(l, r, cur, examine_modes)

    return None

def try_absorption(l, r, cur):
    '''Determines whether [l r -> cur] matches any absorption rules.''' 
    if r.has_feature("conj") and l == r and l == cur:
        return "conjoin" # X X[conj] -> X

    if not l.is_complex():
        if cur.has_feature("conj"):
            if str(l.cat) in ConjPunctuationCats: return "conj_comma_absorb"
            if l.cat == "conj": return "conj_absorb"

        if cur == SbNPbSbNP and l.cat == "," and str(r) == "NP": # , NP -> (S\NP)\(S\NP)
            return "appositive_comma_absorb"
        if str(cur) == "N" and l.cat == "conj" and str(r) == "N":
            return "funny_conj" # conj N -> N is the funny conj rule

        if l.cat in LeftAbsorbedPunctuationCats and r == cur:
            return "l_punct_absorb"

    if not r.is_complex() and r.cat in RightAbsorbedPunctuationCats and l == cur:
        return "r_punct_absorb"

    return None
