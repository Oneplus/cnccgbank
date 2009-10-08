from munge.proc.filter import Filter
from apps.cn.output import *
from munge.trees.traverse import leaves

class PipeFormat(Filter, OutputDerivation):
    def __init__(self, outdir, format):
        Filter.__init__(self)
        OutputDerivation.__init__(self, transformer=self.transformer)
        
        self.outdir = outdir
        self.format_string = self.make_format_string_from(format)
        
    def accept_derivation(self, bundle):
        self.write_derivation(bundle)
        
    def transformer(self, bundle):
        return " ".join(self.format(leaf) for leaf in leaves(bundle.derivation))
    
    @staticmethod
    def make_format_string_from(format):
        substitutions = {
            "%w": "%(lex)s",
            "%p": "%(pos)s",
            "%s": "%(cat)s"
        }
        for src, dst in substitutions.iteritems():
            format = re.sub(src, dst, format)
        return format
        
    def format(self, leaf):
        return self.format_string % {'lex': leaf.lex, 'pos': leaf.pos1, 'cat': str(leaf.cat)}
