import vim
import os
import os.path
from vim_bridge import bridged


#
# General helper functions
#

def _relpath(path, start='.', try_stdlib=True):
    """Returns the relative version of the path.  This is a backport of
    Python's stdlib routine os.path.relpath(), which is not yet available in
    Python 2.4.

    """
    # Fall back onto stdlib version of it, if available
    if try_stdlib:
        try:
            return os.path.relpath(path, start)
        except AttributeError:
            # Python versions below 2.6 don't have the relpath function
            # It's ok, we fall back onto our own implementation
            pass

    fullp = os.path.abspath(path)
    fulls = os.path.abspath(start)
    matchs = os.path.normpath(start)
    if not matchs.endswith(os.sep):
        matchs += os.sep

    if fullp == fulls:
        return '.'
    elif fullp.startswith(matchs):
        return fullp[len(matchs):]
    else:
        # Strip dirs off of fulls until it is a prefix of fullp
        path_prefixes = []
        while True:
            path_prefixes.append(os.path.pardir)
            fulls = os.path.dirname(fulls)
            if fullp.startswith(fulls):
                break
        remainder = fullp[len(fulls):]
        if remainder.startswith(os.sep):
            remainder = remainder[len(os.sep):]
        path_prefix = os.sep.join(path_prefixes)
        return os.path.join(path_prefix, remainder)


def strip_prefix(s, prefix):
    if prefix != "" and s.startswith(prefix):
        return s[len(prefix):]
    else:
        return s


def is_home_dir(path):
    return os.path.realpath(path) == os.path.expandvars("$HOME")


def is_fs_root(path):
    return os.path.realpath(path) == "/" or \
           (int(vim.eval("g:ProjRootStopAtHomeDir")) and is_home_dir(path))


def find_project_root(path='.'):
    if not os.path.isdir(path):
        return find_project_root(os.path.dirname(os.path.realpath(path)))

    indicators = vim.eval("g:ProjRootIndicators")
    while not is_fs_root(path):
        for i in indicators:
            if os.path.exists(os.path.join(path, i)):
                return os.path.realpath(path)
        path = os.path.join(path, os.path.pardir)
    raise Exception("Could not find project root")


#
# Classes that implement TestLayouts
#

class BaseTestLayout(object):
    def __init__(self):
        self.source_root = vim.eval('g:PyUnitSourceRoot')
        self.test_root = vim.eval('g:PyUnitTestsRoot')
        self.prefix = vim.eval('g:PyUnitTestPrefix')


    # Helper methods, to be used in subclasses
    def break_down(self, path):
        parts = path.split(os.sep)
        if len(parts) > 0:
            if parts[-1] == '__init__.py':
                del parts[-1]
            elif parts[-1].endswith(".py"):
                parts[-1] = parts[-1][:-len(".py")]
        return parts

    def glue_parts(self, parts, use_under_under_init=False):
        if use_under_under_init:
            parts = parts + ['__init__.py']
        else:
            parts = parts[:-1] + [parts[-1] + '.py']
        return os.sep.join(parts)

    def relatize(self, path):
        return _relpath(path, find_project_root())

    def absolutify(self, path):
        if os.path.isabs(path):
            return path
        return os.sep.join([find_project_root(), path])


    # The actual BaseTestLayout methods that need implementation
    def is_test_file(self, some_file):
        raise NotImplemented("Implement this method in a subclass.")

    def get_test_file(self, source_file):
        raise NotImplemented("Implement this method in a subclass.")

    def get_source_candidates(self, test_file):
        raise NotImplemented("Implement this method in a subclass.")

    def get_source_file(self, test_file):
        for candidate in self.get_source_candidates(test_file):
            if os.path.exists(candidate):
                return candidate
        raise RuntimeError("Source file not found.")


class SideBySideLayout(BaseTestLayout):
    def is_test_file(self, some_file):
        some_file = self.relatize(some_file)
        parts = self.break_down(some_file)
        filepart = parts[-1]
        return filepart.startswith(self.prefix)

    def get_test_file(self, source_file):
        source_file = self.relatize(source_file)
        parts = self.break_down(source_file)
        parts[-1] = self.prefix + parts[-1]
        return self.glue_parts(parts)

    def get_source_candidates(self, test_file):
        test_file = self.relatize(test_file)
        parts = self.break_down(test_file)
        filepart = parts[-1]
        if not filepart.startswith(self.prefix):
            raise RuntimeError("Not a test file.")
        parts[-1] = filepart[len(self.prefix):]
        return [self.glue_parts(parts)]


class FlatLayout(BaseTestLayout):
    def is_test_file(self, some_file):
        some_file = self.relatize(some_file)
        if not some_file.startswith(self.test_root):
            return False

        some_file = _relpath(some_file, self.test_root)

        parts = self.break_down(some_file)
        if len(parts) != 1:
            return False
        return parts[0].startswith(self.prefix)

    def get_test_file(self, source_file):
        source_file = self.relatize(source_file)
        if not source_file.startswith(self.source_root):
            raise RuntimeError("File %s is not under the source root." % source_file)

        source_file = _relpath(source_file, self.source_root)
        parts = self.break_down(source_file)
        flat_file_name = "_".join(parts)
        parts = [self.test_root] + [self.prefix + flat_file_name]
        return self.glue_parts(parts)

    def get_source_candidates(self, test_file):
        test_file = self.relatize(test_file)
        if not test_file.startswith(self.test_root):
            raise RuntimeError("File %s is not under the test root." % test_file)

        test_file = _relpath(test_file, self.test_root)
        parts = self.break_down(test_file)
        if len(parts) != 1:
            raise RuntimeError("Flat tests layout does not allow tests to be more than one directory deep.")
        file_name = strip_prefix(parts[0], self.prefix)
        parts = file_name.split("_")
        parts = [self.source_root] + parts
        return [self.glue_parts(parts, x) for x in (False, True)]


class FollowHierarchyLayout(BaseTestLayout):
    def is_test_file(self, some_file):
        some_file = self.relatize(some_file)
        if not some_file.startswith(self.test_root):
            return False

        some_file = _relpath(some_file, self.test_root)

        parts = self.break_down(some_file)
        for p in parts:
            if not p.startswith(self.prefix):
                return False
        return True

    def get_test_file(self, source_file):
        source_file = self.relatize(source_file)
        if not source_file.startswith(self.source_root):
            raise RuntimeError("File %s is not under the source root." % source_file)

        source_file = _relpath(source_file, self.source_root)
        parts = self.break_down(source_file)
        parts = map(lambda p: self.prefix + p, parts)
        parts = [self.test_root] + parts
        return self.glue_parts(parts)

    def get_source_candidates(self, test_file):
        test_file = self.relatize(test_file)
        if not test_file.startswith(self.test_root):
            raise RuntimeError("File %s is not under the test root." % test_file)

        test_file = _relpath(test_file, self.test_root)
        parts = self.break_down(test_file)
        parts = [strip_prefix(p, self.prefix) for p in parts]
        parts = [self.source_root] + parts
        return [self.glue_parts(parts, x) for x in (False, True)]


def get_implementing_class():
    implementations = {
        'flat': FlatLayout,
        'follow-hierarchy': FollowHierarchyLayout,
        'side-by-side': SideBySideLayout,
    }
    test_layout = vim.eval('g:PyUnitTestsStructure')
    try:
        return implementations[test_layout]
    except KeyError:
        raise RuntimeError('No such test layout: %s' % test_layout)


#
# The main functions
#

def get_test_file_for_source_file(path):
    impl = get_implementing_class()()
    return impl.get_test_file(path)


def find_source_file_for_test_file(path):
    impl = get_implementing_class()()
    for f in impl.get_source_candidates(path):
        if os.path.exists(f):
            return f
    raise Exception("Source file not found.")


def is_test_file(path):
    impl = get_implementing_class()()
    return impl.is_test_file(path)


def _vim_split_cmd(inverted=False):
    invert = {'top': 'bottom', 'left': 'right',
              'right': 'left', 'bottom': 'top', 'no': 'no'}
    mapping = {'top': 'lefta', 'left': 'vert lefta',
               'right': 'vert rightb', 'bottom': 'rightb', 'no': ''}
    splitoff_direction = vim.eval("g:PyUnitTestsSplitWindow")
    if inverted:
        return mapping[invert[splitoff_direction]]
    else:
        return mapping[splitoff_direction]


def _open_buffer_cmd(path, opposite=False):
    splitopts = _vim_split_cmd(opposite)
    if not splitopts:
        splitcmd = 'edit'
    elif int(vim.eval('bufexists("%s")' % path)):
        splitcmd = splitopts + ' sbuffer'
    else:
        splitcmd = splitopts + ' split'
    command = "%s %s" % (splitcmd, path)
    return command


def lcd_to_project_root(path):
    vim.command("lcd %s" % find_project_root(path))


def switch_to_test_file_for_source_file(path):
    testfile = get_test_file_for_source_file(path)
    testdir = os.path.dirname(testfile)
    if not os.path.isfile(testfile):
        if int(vim.eval('g:PyUnitConfirmTestCreation')):
            # Ask the user for confirmation
            rel_testfile = _relpath(testfile, find_project_root(path))
            msg = 'confirm("Test file does not exist yet. Create %s now?", "&Yes\n&No")' % rel_testfile
            if int(vim.eval(msg)) != 1:
                return

        # Create the directory up until the file (if it doesn't exist yet)
        if not os.path.exists(testdir):
            os.makedirs(testdir)

    vim.command(_open_buffer_cmd(testfile))
    lcd_to_project_root(path)


def switch_to_source_file_for_test_file(path):
    sourcefile = find_source_file_for_test_file(path)
    vim.command(_open_buffer_cmd(sourcefile, opposite=True))
    lcd_to_project_root(path)


@bridged
def PyUnitSwitchToCounterpartOfFile(path):
    if is_test_file(path):
        switch_to_source_file_for_test_file(path)
    else:
        switch_to_test_file_for_source_file(path)


@bridged
def PyUnitRunTestsForFile(path):
    if not is_test_file(path):
        path = get_test_file_for_source_file(path)
    relpath = _relpath(path, '.')
    vim.command('call PyUnitRunTestsForTestFile("%s")' % relpath)
