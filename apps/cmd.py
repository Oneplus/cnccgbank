# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

import glob, readline, re, sys, os
import subprocess

try:
    from cmd2 import options, make_option
except ImportError:
    def options(f):
        def _f(*args, **kwargs): pass
        return _f
    def make_option(*args, **kwargs): pass
    import cmd

from munge.proc.trace_core import TraceCore
from munge.proc.dynload import get_argcount_for_method
from apps.util.cmd_utils import DefaultShell, HistorySavingDefaultShell
from munge.util.iter_utils import flatten
from munge.util.err_utils import warn, info, msg, err
from munge.util.list_utils import list_preview
from munge.proc.tgrep.tgrep import Tgrep, SmallSentenceThreshold, SmallSubtreeThreshold
import munge.proc.trace as T

from munge.util.config import config

BuiltInPackages = T.BuiltInPackages
DefaultPager = '/usr/bin/less' # pager to use if $PAGER not set

def filter_run_name(filter_name, filter_args):
    '''Produces a human-readable summary of a filter run: the filter name with a list of its arguments
in parentheses separated by commas.'''
    return "%s(%s)" % (filter_name, ', '.join(filter_args) if filter_args else '')

PagerFilename = 'pager'
StdoutFilename = 'stdout'
class Shell(HistorySavingDefaultShell):
    '''A shell interface to trace functionality.'''
    def __init__(self, pager_path=None, files=None, verbose=True, clear_history=False):
        HistorySavingDefaultShell.__init__(self, clear_history=clear_history)

        self.tracer = TraceCore(libraries=BuiltInPackages, verbose=verbose, reader_class_name=config.cmd_reader_class)
        self.prompt = "trace> "

        self.files = files or []

        self.last_exception = None

        self._verbose = verbose

        if pager_path:
            self.pager_path = pager_path
            self.output_file = PagerFilename
        else:
            self.pager_path = self.output_file = None

    def get_verbose(self): return self._verbose
    def set_verbose(self, is_verbose):
        self._verbose = self.tracer.verbose = is_verbose
    verbose = property(get_verbose, set_verbose)

    def do_quiet(self, args):
        '''Produces less output during processing.'''
        if self._verbose:
            self.set_verbose(False)
            msg("Will generate less output.")

    def do_verbose(self, args):
        '''Produces more output during processing.'''
        if not self._verbose:
            self.set_verbose(True)
            msg("Will generate more output.")

    def preloop(self):
        '''Executed before the command loop is entered.'''
        DefaultShell.preloop(self)
        # remove '-' (for option completion) and a number of shell separators (for path completion)
        # from the set of completer delimiters
        readline.set_completer_delims(re.sub(r'[-/*~\\]', '', readline.get_completer_delims()))

    def precmd(self, line):
        '''Executed before every command is interpreted.'''
        cleaned_line = line.strip()

        self._hist.append(cleaned_line)
        return cleaned_line

    def do_load(self, args):
        '''Loads filter modules given as package names.'''
        modules = args.split()

        old_modules = set(self.tracer.available_filters_dict.keys())
        self.tracer.add_modules(modules)
        modules = set(self.tracer.available_filters_dict.keys())

        added_modules = modules.difference(old_modules)
        if added_modules:
            msg("%s modules added:", len(added_modules))
            for module in added_modules:
                msg("\t%s", module)
        else:
            msg("No modules added.")

    @options([ make_option('-l', '--long', action='store_true', dest='long', help='Show detailed summary', default=False),
               make_option('-s', '--sort-by', action='store', type='choice', choices=['name', 'module', 'opt', 'long-opt'],
                           dest='sort_key', help='Display filters in a given sorted order', default='name')])
    def do_list(self, args, opts):
        """Lists all loaded filters."""
        self.tracer.list_filters(long=opts.long, filter_sort_key=opts.sort_key)

    def do_with(self, args):
        '''Changes or displays the working set.'''
        args = args.split()
        if args:
            self.files = []
            for arg in args:
                # So that if arg is not a glob, it won't get removed
                # because it doesn't exist on the fs:
                globbed = list(flatten(glob.glob(arg)))
                if globbed:
                    self.files += globbed
                else:
                    self.files.append(arg)

        msg("Working set is: " + list_preview(self.files))

    def get_filter_by_switch(self, switch_name):
        '''Retrieves the filter object based on its short or long form switch name.'''
        is_option_long_name = switch_name.startswith('--')

        for filter in self.tracer.available_filters_dict.values():
            if is_option_long_name:
                if filter.long_opt == switch_name[2:]:
                    return filter.__name__
            else:
                if filter.opt == switch_name[1:]:
                    return filter.__name__

        err("No filter with switch %s found.", switch_name)
        return None

    def do_run(self, args):
        '''Runs the given filter with the given arguments on the working set.'''
        args = args.split()

        if not args: return

        filter_name = args.pop(0)
        if not filter_name: # no filter with the requested switch was found
            return
        if filter_name.startswith('--'): # a long option name was given
            filter_name = self.get_filter_by_switch(filter_name)
        elif filter_name.startswith('-'): # a short option name was given
            filter_name = self.get_filter_by_switch(filter_name)

        # Special case: for a one-arg filter any number of arguments are treated
        # as a single argument.
        if (filter_name in self.tracer and
            get_argcount_for_method(self.tracer[filter_name].__init__) == 1):

            filter_args = (' '.join(args), )
        elif args is not None:
            filter_args = args
        else:
            filter_args = None

        def action():
            self.tracer.run( [(filter_name, filter_args)], self.files )
            print

        self.redirecting_stdout(action, filter_name, filter_args)

    def do_runmany(self, args):
        # XXX: HACK HACK HACK HACK
        filters = args.split()
        if not args: return

        def action():
            self.tracer.run( [( filter_name, () ) for filter_name in filters], self.files )
            print

        self.redirecting_stdout(action, '|'.join(filters), ())

    def do_backtrace(self, args):
        '''Displays the exception backtrace for the last failed filter.'''
        if self.last_exception:
            sys.excepthook(*self.last_exception)
    do_bt = do_backtrace

    def create_pager_pipe(self):
        if not self.pager_path:
            raise RuntimeError('No pager was given.')

        if os.path.basename(self.pager_path) == 'less':
            params = (self.pager_path, '-R', '-')
        else:
            params = (self.pager_path, '-')

        return subprocess.Popen(
            params,
            stdin=subprocess.PIPE,
            stdout=None, stderr=None,
            shell=False)

    def do_into(self, args):
        '''Sets or displays the destination for filter output. The special filename
StdoutFilename will redirect filter output to the console.'''
        def print_output_destination():
            if self.output_file is None:
                msg("Filter output will be sent to the console.")
            elif self.output_file == PagerFilename:
                msg("Filter output will be paged with %s.", self.pager_path)
            else:
                msg("Filter output will be redirected to: %s", self.output_file)

        args = args.split(' ', 1)
        output_file = args[0]

        if output_file:
            if output_file == StdoutFilename:
                self.output_file = None
            else: # we will treat the value PagerFilename specially
                self.output_file = output_file

        print_output_destination() # report on output destination in any case

    def redirecting_stdout(self, action, filter_name, filter_args):
        '''Calls the given _action_ with stdout temporarily redirected to _self.output_file_ or
a pager program.'''
        try:
            old_stdout = sys.stdout

            pipe = None

            if self.output_file == PagerFilename:
                pipe = self.create_pager_pipe()
                sys.stdout = pipe.stdin
            elif self.output_file:
                sys.stdout = open(self.output_file, 'w')

            action()

            if self.output_file == PagerFilename:
                if pipe:
                    sys.stdout.close() # Signal EOF
                    pipe.wait()

        except KeyboardInterrupt:
            if pipe:
                pipe.stdin.close()
                pipe.wait()

            msg("\nFilter run %s halted by user.", filter_run_name(filter_name, filter_args))

        except Exception, e:
            if pipe:
                pipe.stdin.close()
                pipe.wait()

            msg("Filter run %s halted by framework:", filter_run_name(filter_name, filter_args))
            # TODO: Exception no longer has a message field in Python 3.0, produces a DeprecationWarning
            # under Python 2.7
            msg("\t%s (%s)", e.message, e.__class__.__name__)

            self.last_exception = sys.exc_info()
        finally:
            sys.stdout = old_stdout

            if pipe:
                pipe.stdin.close()

    @options([ make_option('-S', '--pp-subtree', help='Pretty print each matching subtree.',
                           dest='show_mode', action='store_const', const='pp_subtree', default='pp_subtree'),
               make_option('-s', '--subtree', help='Print each matching subtree only.',
                           dest='show_mode', action='store_const', const='subtree'),
               make_option('-w', '--whole-tree', help='Print whole tree on match (not just matching subtrees).',
                           dest='show_mode', action='store_const', const='whole_tree'),
               make_option('-W', '--pp-whole-tree', help='Pretty print whole tree on match (not just matching subtrees).',
                           dest='show_mode', action='store_const', const='pp_whole_tree'),
               make_option('-y', '--synttree', help='Pretty print as TikZ/QTree LaTeX.',
                           dest='show_mode', action='store_const', const='pp_synttree'),

               make_option('-m', '--matched-tag', help='Print matched tag.',
                           dest='show_mode', action='store_const', const='matched_tag'),

               make_option('-b', '--tags-and-text', help='Print tree tags and text under.',
                           dest='show_mode', action='store_const', const='tags_and_text'),

               make_option('-T', '--tags', help='Print tree tags.',
                           dest='show_mode', action='store_const', const='tags'),

               make_option('-t', '--tokens', help='Print tokens of matching trees.',
                           dest='show_mode', action='store_const', const='tokens'),
               make_option('-r', '--rule', help='Shows the local category context of the match.',
                           dest='show_mode', action='store_const', const='rule'),
               make_option('-n', '--none', help='Print nothing on each match (captions may still be printed).',
                           dest='show_mode', action='store_const', const='none'),
                           
               make_option('-l', '--label', help='On match: print derivation label.',
                           dest='caption_modes', action='append_const', const=Tgrep.CAPTION_LABEL),
               make_option('-L', '--length', help='On match: print word count of derivation',
                           dest='caption_modes', action='append_const', const=Tgrep.CAPTION_NWORDS),
               make_option('--caption-space', help='On match: print a space',
                           dest='caption_modes', action='append_const', const=Tgrep.CAPTION_SPACE),
               make_option('--caption-newline', help='On match: print a newline',
                           dest='caption_modes', action='append_const', const=Tgrep.CAPTION_NEWLINE),
               make_option('-0', '--no-caption', help='On match: print no caption',
                           dest='print_caption', action='store_false', default=True),

               make_option('-a', '--find-all', help='Find all matches (not just the first).',
                           dest='find_mode', action='store_const', const=Tgrep.FIND_ALL, default=Tgrep.FIND_ALL),
               make_option('--find-top', help='Only match against the root node.',
                           dest='find_mode', action='store_const', const=Tgrep.FIND_TOP),
               make_option('-3', '--find-small-sents', 
                           help=('Find only matches in small sentences (%d or fewer words)' % SmallSentenceThreshold),
                           dest='find_mode', action='store_const', const=Tgrep.FIND_SMALL_SENTS),
               make_option('-2', '--find-small', help=('Find all small subtree matches (%d or fewer leaves).' % SmallSubtreeThreshold),
                           dest='find_mode', action='store_const', const=Tgrep.FIND_SMALL),
               make_option('-1', '--find-first', help='Match only one node where possible.',
                           dest='find_mode', action='store_const', const=Tgrep.FIND_FIRST) ])
    def do_tgrep(self, args, opts):
        '''Performs a tgrep query.'''
        if not args.strip(): return

        show_mode = {
            'subtree':       'node',
            'pp_subtree':    'pp_node',
            'whole_tree':    'tree',
            'pp_whole_tree': 'pp_tree',
            'pp_synttree': 'pp_synttree',
            'tokens':     'tokens',
            'rule':       'rule',
            'tags':       'tags',
            'tags_and_text':'tags_and_text',
            'matched_tag':'matched_tag',
            'none': 'none'
        }[opts.show_mode]
        
        # if we passed -0/--no-caption, suppress all caption printing
        if not opts.print_caption:
            caption_modes = []
        # otherwise, if the user didn't pass in any caption specifiers, use Tgrep's defaults by passing it None
        elif not opts.caption_modes:
            caption_modes = None
        else:
            caption_modes = opts.caption_modes

        def action():
            tgrep_filter = Tgrep(args, show_mode=show_mode, find_mode=opts.find_mode, caption_modes=caption_modes)
            self.tracer.run_filters((tgrep_filter, ), self.files)

        self.redirecting_stdout(action, 'Tgrep', (args, ))

    do_tg = do_tgrep

    def default(self, args):
        self.do_run(args)

    def completedefault(self, *args):
        return self.complete_run(*args)

    def get_filter_attributes(self, attr):
        return [getattr(filter, attr) for filter in self.tracer.available_filters_dict.values()]

    def get_long_forms(self):
        return ["--" + long_opt for long_opt in self.get_filter_attributes('long_opt')]

    def get_short_forms(self):
        return ["-" + opt for opt in self.get_filter_attributes('opt')]

    def complete_run(self, text, line, begin_index, end_index):
        '''Returns completions for the _run_ command: either a long option name, a short one, or a filter name.'''
        # Be careful with the cmd module; it seems to swallow all getattr exceptions silently (eg accessing
        # a non-existent member of this class succeeds)
        if text.startswith('--'):
            return [opt for opt in self.get_long_forms() if opt.startswith(text)]
        elif text.startswith('-'):
            return [opt for opt in self.get_short_forms() if opt.startswith(text)]
        else: # completing a filter name or a filter argument
            # Case insensitive comparison here
            filter_names = [name for name in self.tracer.available_filters_dict.keys() if name.lower().startswith(text.lower())]
            return filter_names

    def complete_with(self, text, line, begin_index, end_index):
        '''Returns completions for the _with_ command: paths of which the given text is a prefix.'''
        # TODO: make optionally case-insensitive. Is there a better way short of giving a glob [Ll][Ii][Kk][Ee] this?
        return self.filename_complete(text)

    def complete_load(self, text, line, begin_index, end_index):
        '''Returns completions for the _load_ command: all modules available to Python.'''
        return [module for module in sys.modules.keys() if module.startswith(text)]

    def filename_complete(self, text):
        '''Returns a list of files and directories whose names are prefixes of the entered
text. Appends a directory separator to directory completions.'''
        return [path + (os.path.sep if os.path.isdir(path) else '')
                for path in glob.glob(text + '*')
                if path.startswith(text)]

def run_file(option, opt_string, value, parser, *args, **kwargs):
    '''Reads and invokes commands from a file, then terminates.'''
    script_file = value
    if not os.path.exists(script_file):
        raise RuntimeError('Script file %s not found.' % script_file)

    sh = Shell()
    for line in open(script_file):
        line = line.strip()
        sh.onecmd(line)

    sys.exit()

def set_config_file(option, opt_string, value, parser, *args, **kwargs):
    try:
        config.config_file = value
    except IOError, e:
        err("Couldn't load config file `%s': %s", value, e)

def register_builtin_switches(parser):
    parser.add_option('-F', '--file-script', help='Reads and invokes cmd.py commands from a file, then terminates. Ignores input files given on the command line.',
                      type='string', nargs=1, action='callback', callback=run_file)
    parser.add_option('-c', '--config', help="Set config file.", type='string', nargs=1,
                      action='callback', callback=set_config_file)
    parser.add_option('-p', '--pager', help='Feeds filter output through the specified pager (default: $PAGER or %s).'% DefaultPager,
                      type='string', nargs=1, default=(os.getenv('PAGER') or DefaultPager), dest='pager_path')
    parser.add_option('--no-pager', help='Filter output is redirected to stdout and not a pager.', action='store_const', dest='pager_path', const=None)
    parser.add_option('-v', '--verbose', help='Print diagnostic messages.',
                      action='store_true', dest='verbose', default=False)
    parser.add_option("-b", "--break-on-error", help="Ignore the rest of the document if an error is encountered.",
                      action='store_true', dest='break_on_exception', default=False)
    parser.add_option('-q', '--quiet', help='Make less output.',
                      action='store_false', dest='verbose')
    parser.add_option('-H', '--clear-history', help='Clear the history file.',
                      action='store_true', dest='clear_history')

from optparse import OptionParser
if __name__ == '__main__':
    try:
        import psyco
        psyco.full()
    except ImportError: pass

    parser = OptionParser(conflict_handler='resolve')
    parser.set_defaults(verbose=True, clear_history=False)
    register_builtin_switches(parser)

    opts, remaining_args = parser.parse_args(sys.argv)
    argv = remaining_args[1:] # Take any remaining arguments as input files to start with

    parser.destroy()

    sh = Shell(pager_path=opts.pager_path,
               files=argv,
               verbose=opts.verbose,
               clear_history=opts.clear_history)
    sh.cmdloop()
