# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

import random
random.seed()

def first_index_such_that(pred, l):
    '''Finds the first index satisfying the given predicate, or None if no index does.'''
    for i, e in enumerate(list(l)):
        if pred(e): return i
    return None
    
def last_index_such_that(pred, l):
    '''Finds the last index satisfying the given predicate (counted from the end) satisfying
the given predicate, or None if no index does.'''
    return first_index_such_that(pred, reversed(list(l)))
    
def is_sublist(smaller, larger):
    '''Implements naive string matching.'''
    m = len(smaller)
    for start in range(0, (len(larger) - m + 1) + 1):
        if larger[start:(start+m)] == smaller: return True
        
    return False
    
def find(pred, l):
    '''Finds an element of _l_ which satisfies _pred_.'''
    for e in l:
        if pred(e): return e
        
    return None
    
def where(pred, seq):
    '''An iterator over elements of _seq_ which satisfy _pred_.'''
    for e in seq:
        if pred(e): yield e
    
def starmap(f, l):
    '''Given a sequence ((A1, B1, ...), (A2, B2, ...)) and a function (A, B, ...) -> C, this returns
a sequence (C1, C2, ...).'''
    for e in l: f(*e)
    
def transpose(xs):
    '''Transposes a list of lists.'''
    return map(list, zip(*xs))

def preserving_zip(*orig_seqs):
    '''A preserving zip which does not truncate to the length of the shortest sequence like the standard zip.
    seq1, seq2 = (1, 2), (3, 4, 5)
    zip(seq1, seq2) => ((1, 3), (2, 4))
    preserving_zip(seq1, seq2) => ((1, 3), (2, 4), (None, 5))'''
    seqs = map(lambda e: list(e)[::-1], orig_seqs)
    result = []
    
    def maybe_pop(seq):
        if not seq: return None
        else: return seq.pop()
        
    while any(seqs): # While some sequence is not empty
        result.append(map(maybe_pop, seqs))
    
    return result
    
def list_preview(orig_l, head_elements=7, tail_elements=1):
    '''Makes a short preview string from a list, showing a given number of elements from its head and tail.'''
    if not orig_l: return "{}"

    l = sorted(orig_l[:])
    tail = l[-tail_elements:]
    del l[-tail_elements:] # Ensure that no overlap between head and tail happens, by deleting tail first
    head = l[0:head_elements]

    bits = ["{ "]
    if head: 
        bits += ", ".join(str(e) for e in head)
    if tail:
        if head:
            bits.append(", ..., ")
        bits += ", ".join(str(e) for e in tail)
    bits.append(" }")

    return ''.join(bits)
    
def intersperse(l, spacer=", "):
    '''Given a list _l_, intersperses the given _spacer_ between each pair of elements.'''
    for i in xrange(len(l)-1, 0, -1):
        l.insert(i, spacer)
    return l

class FixedSizeList(list):
    '''A list which holds at most a given number of elements. Attempts to add further elements are no-ops.'''
    def __init__(self, maximum_capacity=10):
        self.maximum_capacity = maximum_capacity
    def append(self, v):
        if len(self) < self.maximum_capacity:
            list.append(self, v)
            
class FixedSizeRandomList(list):
    def __init__(self, maximum_capacity=10):
        self.maximum_capacity = maximum_capacity
        self.n = 0
    def append(self, v):
        if len(self) < self.maximum_capacity:
            list.append(self, v)
        else:
            j = random.randint(0, self.n-1)
            if j < self.maximum_capacity:
                self[j] = v
                
        self.n += 1