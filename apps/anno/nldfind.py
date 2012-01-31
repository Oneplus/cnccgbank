import sys
import traceback
import os

from munge.proc.filter import Filter
from apps.cn.output import *
from munge.util.tgrep_utils import get_first
from munge.proc.tgrep.tgrep import find_all
from munge.trees.traverse import leaves
from munge.trees.pprint import pprint_with
from munge.util.colour_utils import bold, codes

'''
if (self.resumer.current_index_for(nld_type, bundle.label()) < match_index) and \
   (not self.resumer.was_skipped(nld_type, match_index, bundle.label())): 
   continue

indices = self.get_dep(match, ctx, nld_type=nld_type, pprint=pprint)
if indices is not None:
    head_index, arg_index = indices
    print >>self.anno, self.Template % (bundle.label(), head_index, arg_index, nld_type)
else:
    self.resumer.add_skipped(bundle.label(), nld_type, match_index)
    '''
class Resumer(object):
    def __init__(self, resumer_fn):
        self.fn   = resumer_fn
        if os.path.isfile(resumer_fn):
            self.resumer_state = self.read_state(resumer_fn)
        else:
            self.resumer_state = {} # needs to keep 'skipped' status for each label + nld_type, and 'current index' for each label + nld_type
            
    def was_skipped(self, nld_type, match_index, label):
        # key 'skipped nld_type match_index label' exists?
        key = 'skipped %s %s %s' % (nld_type, match_index, label)
        return self.resumer_state.has_key(key)
        
    def add_skipped(self, nld_type, match_index, label):
        # add 'skipped nld_type match_index label' key
        key = 'skipped %s %s %s' % (nld_type, match_index, label)
        self.resumer_state[key] = 1
        
    def remove_skipped(self, nld_type, match_index, label):
        key = 'skipped %s %s %s' % (nld_type, match_index, label)
        del self.resumer_state[key]
        
    def current_index_for(self, nld_type, label):
        # get value for key 'index nld_type label' or return -1
        key = 'index %s %s' % (nld_type, label)
        return self.resumer_state.get(key, -1)
        
    def set_current_index_for(self, nld_type, label, match_index):
        # set value for key 'index nld_type label'
        key = 'index %s %s' % (nld_type, label)
        self.resumer_state[key] = match_index        
            
    def read_state(self, fn):
        state = {}
        
        with file(fn, 'r') as f:
            for line in f:
                line = line.rstrip()
                key, value = line.split('|', 2)
                state[key] = int(value)
                
        return state
    
    def save_state(self, fn=None):
        if fn is None: fn = self.fn
        
        with file(fn, 'w') as f:
            for key, value in self.resumer_state.iteritems():
                print >>f, '%s|%s' % (key, value)

class NLDFinder(Filter):
    Patterns = [
    # F = filler
    # T = trace
    # V = verb
        (r'* < { /CP/ <1 { /WHNP/ < { "-NONE-" & ^/\*OP\*/=T } } < { /CP/ < { /IP/ << { /NP-OBJ/ < { "-NONE-" & ^/\*T\*-\d+/ } $ /V[VECA]|VRD|VSB|VCD/=V } } < /DEC/ } }', 'objex'),
        (r'* < { /CP/ <1 { /WHNP/ < { "-NONE-" & ^/\*OP\*/=T } } < { /CP/ < { /IP/ << { /NP-SBJ/ < { "-NONE-" & ^/\*T\*-\d+/ } $ /VP/=V } } < /DEC/ } }', 'subjex'),
        (r'* < { /CP/ <1 { /WHNP/ < { "-NONE-" & ^/\*OP\*/=T } } < {          /IP/ << { /NP-OBJ/ < { "-NONE-" & ^/\*T\*-\d+/ } $ /V[VECA]|VRD|VSB|VCD/=V } } }', 'objex_null'),
        (r'* < { /CP/ <1 { /WHNP/ < { "-NONE-" & ^/\*OP\*/=T } } < {          /IP/ << { /NP-SBJ/ < { "-NONE-" & ^/\*T\*-\d+/ } $ /VP/=V } } }', 'subjex_null'),
        # (r'/IP/ < /-TPC-\d+/a=F << { * < { "-NONE-" & ^/\*T\*-\d+/=T } $ /V/=V }', 'gaptop'),
        # (r'/LB/ $ { /IP/ << { "-NONE-" & ^/\*-\d+/=T } }', 'lb_gap'),
        # (r'/LB/ $ /IP/', 'lb_nongap'),
        # (r'/SB/ $ { /IP/ << { "-NONE-" & ^/\*-\d+/=T } }', 'sb_gap'),
        # (r'/SB/ $ /VP/', 'sb_nongap'),
    ]
    # create an interface which shows you the context of the nld
    # asks you to identify the filler of V
    # then writes out
    #   head filler nld_type deriv_id
    # lines to a file
    # NOTE: head may be unfilled (e.g. in 'shi e V de', the subject of V is not filled)
    
    # resuming annotation
    # how to resume at a certain point?
    #   
    # how to return to missing annotations?
    # if we add new NLD types to annotate, how do we skip over the ones which have been done?
    
    @staticmethod
    def one_node(node):
        if node.is_leaf():
            return node.lex
        else:
            return ' '.join(node.text())
            
    def get_dep(self, match, ctx, pprint, nld_type, bundle):
        node = match

        while True:
            print pprint(node, focus=ctx.v)
            print '(head index, arg index) for head phrase %s' % self.one_node(ctx.v)
            print 'head-arg relation: %s' % nld_type
            print '>',
            response = raw_input().rstrip()
            if response == 'u':
                if node.parent:
                    node = node.parent
                else:
                    print 'at root'
            
            elif response.startswith('d'):
                bits = response.split(' ', 2)
                if len(bits) != 2:
                    print 'missing index'
                else:
                    _, index = bits
                    index = int(index)
                
                    if node.is_leaf():
                        print 'at leaves'
                    else:
                        if 0 <= index < node.count():
                            node = node[index]
                        else:
                            print 'invalid index'
                    
            elif response == 'l':
                print 'derivation: %s %s' % (bundle.label(), nld_type)
                print ' '.join(node.text())
                
            elif response == 's':
                return None

            else:
                try:
                    head, arg = map(int, response.split(' ', 2))
                    return head, arg
                except ValueError:
                    print 'not an index'
    
    Template = "%s %s %s %s"
    ResumerTemplate = "%s %s %s"
    # what do we do with the output?
    
    def handle_match(self, pattern, node, bundle, nld_type, pprint_node_repr):
        pprint = pprint_with(pprint_node_repr)
        
        # to resume
        # store the derivation id, the index of the match and the nld_type
        # e.g.
        # 3:3(3) subjex 3 means
        # the annotator stopped at the third subjex case of 3:3(3)
        # there may be '?' entries for previous cases
        for match_index, (match, ctx) in enumerate(find_all(node, pattern, with_context=True)):
            was_skipped = self.resumer.was_skipped(nld_type, match_index, bundle.label())
            current_index = self.resumer.current_index_for(nld_type, bundle.label())
            #                                               0         <= 0
            already_annotated = current_index != -1 and current_index <= match_index
            
            if already_annotated and not was_skipped:
               continue
            
            indices = self.get_dep(match, ctx, nld_type=nld_type, pprint=pprint, bundle=bundle)
            if indices is not None:
                head_index, arg_index = indices
                print >>self.anno, self.Template % (bundle.label(), head_index, arg_index, nld_type)
                
                if was_skipped:
                    self.resumer.remove_skipped(nld_type, match_index, bundle.label())
            else:
                self.resumer.add_skipped(nld_type, match_index, bundle.label())
                
            self.resumer.set_current_index_for(nld_type, bundle.label(), match_index)
        
    def accept_derivation(self, bundle):
        root = bundle.derivation
        
        leaf_map = dict( (v,i) for (i,v) in enumerate(leaves(root)) )
        
        # prints the leaf index next to each leaf
        def index_node_repr(node, compress=False):
            if node.is_leaf():
                return "%s %s %s%s" % (node.tag, node.lex, bold( str(leaf_map[node]) ), codes['reset'])
            else:
                return "%s%s" % (node.tag, codes['reset'])
        
        try:    
            for (pattern, nld_type) in self.Patterns:
                self.handle_match(pattern, root, bundle, nld_type, pprint_node_repr=index_node_repr)
        except Exception, e:
            traceback.print_exc()
        finally:
            self.resumer.save_state()
            
    def __init__(self, anno_fn, resumer_fn):
        Filter.__init__(self)
        self.anno = file(anno_fn, 'w')
        self.resumer = Resumer(resumer_fn)