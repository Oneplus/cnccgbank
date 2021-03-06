# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

from apps.cn.fix import Fix
from apps.cn.fix_utils import *
from munge.cats.cat_defs import N, NP, SfS
import munge.penn.aug_nodes as A
from apps.util.echo import echo

import copy

def _insert_unary(new_P_cat, new_N_cat):
    '''Returns a fix method which, when given a node, sandwiches a node with
category _new_N_cat_ between that node and its children, then re-labels that
node with category _new_P_cat_.'''
    def _fix(self, node, p):
        new_N = copy.copy(p)
        new_N.category = new_N_cat

        pp = p.parent

        if pp:
            replace_kid(pp, p, A.Node(p.tag, [new_N], new_P_cat, head_index=0))
        else:
            return A.Node(p.tag, [new_N], new_P_cat, head_index=0)
            
    return _fix

class FixNP(Fix):
    def pattern(self):
        return [
            (r'@"NP"=P <1 @/\/N$/a=L <2 @"NP"=R', self.fix1),
            (r'*=P <1 @/\/NP$/a=L <2 @"N"=R', self.fix2),
            (r'*=P <2 @/\\NP$/a=R <1 @"N"=L', self.fix3),
            (r'@"NP"=P <2 @/^N\\/', self.fix_np),
            (r'@"NP"=P <1 @"N/N" <2 @"N"', self.fix_np),
            (r'@"NP"=P <1 @"N" <2 @"N[conj]"', self.fix_np),
            (r'@"S/S"=P <1 @"NP" <2 @"NP"', self.fix_topicalised_apposition),
            
            # bunch of N/N < N unary rules due to annotation noise (22:58(1))
            (r'* < { @"N/N" < @"N"=N #<1 }=P', self.fix_nfn_n),
        ]
    
    def __init__(self, outdir):
        Fix.__init__(self, outdir)
        
    def fix_nfn_n(self, pp, p, n):
        replace_kid(pp, p, n)
        
    def fix1(self, node, p, l, r):
        r.category = N
        
    # * < /NP N   ---> * < /NP ( NP < N )
    def fix2(self, node, p, l, r):
        return _insert_unary(NP, N)(self, node, r)

    # * < /NP N   ---> * < /NP ( NP < N )
    def fix3(self, node, p, l, r):
        return _insert_unary(NP, N)(self, node, l)
        
    # NP < N/N N  ---> NP < N < N/N N
    fix_np = _insert_unary(NP, N)
    # S/S < NP NP ---> S/S < NP < NP NP
    fix_topicalised_apposition = _insert_unary(SfS, NP)
