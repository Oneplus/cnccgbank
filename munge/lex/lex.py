# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

from pressplit import split

class CPressplitIterator(object):
    '''preserving_split implemented in C.'''
    def __init__(self, str, split_chars, skip_chars, suppressors):
        self.toks = split(str, split_chars, skip_chars, suppressors)
        
    def __iter__(self):
        for tok in self.toks: yield tok
        
    def peek(self):
        if not self.toks: return None
        return self.toks[0]
    
    def next(self):
        if not self.toks: raise StopIteration
        return self.toks.pop(0)
        
    def clear(self):
        self.toks = []
        
class CStackbasedPressplitIterator(object):
    '''preserving_split implemented in C, with the backing reversed to avoid pop() operations from the front.'''
    def __init__(self, str, split_chars, skip_chars, suppressors):
        self.toks = split(str, split_chars, skip_chars, suppressors)
        self.toks.reverse()
        
    def __iter__(self):
        for tok in reversed(self.toks): yield tok
        
    def peek(self):
        if not self.toks: return None
        return self.toks[-1]
    
    def next(self):
        if not self.toks: raise StopIteration
        return self.toks.pop()
        
    def clear(self):
        self.toks = []

class EagerPressplitIterator(object):
    '''preserving_split implemented in Python with the token stream as a list.'''
    def __init__(self, str, split_chars, skip_chars, suppressors):
        def _preserving_split():
            result = []
            
            use_suppressors = len(suppressors) == 2

            in_node = False
            cur = []
            for char in str:
                if (not in_node and char in split_chars) or \
                        char in skip_chars or \
                        char in suppressors:
                    if cur: 
                        result.append(''.join(cur))
                        del cur[:]

                    if use_suppressors:
                        if char == suppressors[0]: in_node = True
                        elif char == suppressors[1]: in_node = False

                    if char in split_chars or char in suppressors: result.append(char)
                else:
                    cur.append(char)

            if cur: result.append(''.join(cur))
            
            return result

        self.backing = _preserving_split()

    def __iter__(self):
        for token in self.backing: yield token

    def peek(self): 
        if not self.backing: return None
        return self.backing[0]
        
    def next(self):
        if not self.backing: raise StopIteration
        return self.backing.pop(0)
        
    def clear(self):
        self.backing = []
        
class PressplitIterator(object):
    '''preserving_split implementation with the token stream as a generator.'''
    def __init__(self, str, split_chars, skip_chars, suppressors):
        def _preserving_split():
            use_suppressors = len(suppressors) == 2

            in_node = False
            cur = []
            for char in str:
                if (not in_node and char in split_chars) or \
                        char in skip_chars or \
                        char in suppressors:
                    if cur: 
                        yield ''.join(cur)
                        del cur[:]

                    if use_suppressors:
                        if char == suppressors[0]: in_node = True
                        elif char == suppressors[1]: in_node = False

                    if char in split_chars or char in suppressors: yield char
                else:
                    cur.append(char)

            if cur: yield ''.join(cur)

        self.generator = _preserving_split()

        # generator may be empty and raise StopIteration
        try:
            self.top = self.generator.next()
        except StopIteration:
            self.top = None

    def __iter__(self): return self

    def peek(self): return self.top
    def next(self):
        if self.top is None: 
            raise StopIteration

        previous_top = self.top
        try:
            self.top = self.generator.next()
        except StopIteration: 
            self.top = None

        return previous_top
        
    def clear(self):
        self.generator = None

def preserving_split(str, split_chars, skip_chars=" \t\r\n", suppressors='', lexer_class=CStackbasedPressplitIterator):
    '''Returns an iterator yielding successive tokens from _str_ as split on three
    kinds of separators. 
      - _split_chars_ will split the string, and appear in the resulting stream.
      - _skip_chars_ will split the string, but will not appear in the stream.
      - Any text between the pair of _suppressors_ (if given) will be split only
        on skip_chars and not on split_chars.
    The returned iterator supports an additional _peek_ method which returns the same
    value as _next_ without consuming a value from the stream.'''

#    result = lexer_class(str, split_chars, skip_chars, suppressors)
#    print ' '.join(iter(result))
    return lexer_class(str, split_chars, skip_chars, suppressors)

try:
    import psyco
    psyco.bind(preserving_split)
except ImportError: pass
