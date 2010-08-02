import vim
import os
import os.path
from vim_bridge import bridged


def is_home_dir(path):  # {{{
    return os.path.realpath(path) == os.path.expandvars("$HOME")
    # }}}


def is_fs_root(path):  # {{{
    return os.path.realpath(path) == "/" or \
           (int(vim.eval("g:projroot_stop_at_home_dir")) and is_home_dir(path))
    # }}}


def find_project_root(path):  # {{{
    if not os.path.isdir(path):
        return find_project_root(os.path.dirname(os.path.realpath(path)))

    indicators = vim.eval("g:projroot_indicators")
    while not is_fs_root(path):
        for i in indicators:
            if os.path.exists(os.path.join(path, i)):
                return os.path.normpath(path)
        path = os.path.join(path, os.path.pardir)
    raise Exception("Could not find project root")
    # }}}


def find_source_root(path):  # {{{
    source_root = vim.eval("g:source_root")
    return os.path.join(find_project_root(path), source_root)
    # }}}


def _strip_prefix(s, prefix):  # {{{
    if prefix != "" and s.startswith(prefix):
        return s[len(prefix):]
    else:
        return s
    # }}}


def _strip_suffix(s, suffix, replace_by=''):  # {{{
    if suffix != "" and s.endswith(suffix):
        return s[:-len(suffix)] + replace_by
    else:
        return s
    # }}}


def _relpath(path, start='.'):  # {{{
    """Returns the relative version of the path.  This is a backport of
    Python's stdlib routine os.path.relpath(), which is not yet available in
    Python 2.4.

    """
    # Fall back onto stdlib version of it, if available
    try:
        return os.path.relpath(path, start)
    except NameError:
        # Python versions below 2.6 don't have the relpath function
        # It's ok, we fall back onto our own implementation
        pass

    fullp = os.path.abspath(path)
    fulls = os.path.abspath(start)
    matchs = os.path.normpath(start) + os.sep
    print fullp
    print fulls

    if fullp.startswith(matchs):
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
    # }}}


def get_relative_source_path(path, allow_outside_root=False):  # {{{
    root = find_source_root(path)
    if allow_outside_root or os.path.realpath(path).startswith(root):
        return _relpath(path, root)
    else:
        raise Exception('Path %s is not in the source root.' % path)
    # }}}


def get_tests_root(path):  # {{{
    loc = vim.eval("g:tests_root")
    return os.sep.join([find_project_root(path), loc])
    # }}}


def add_test_prefix_to_all_path_components(path):  # {{{
    prefix = vim.eval("g:test_prefix")
    components = path.split(os.sep)
    return os.sep.join([s and prefix + s or s for s in components])
    # }}}


def get_test_file_for_source_file(path):  # {{{
    prefix = vim.eval("g:test_prefix")

    relpath = get_relative_source_path(path)
    relpath = _strip_suffix(relpath, os.sep + '__init__.py', '.py')

    tests_structure = vim.eval("g:tests_structure")
    if tests_structure == "flat":
        u_relpath = relpath.replace("/", "_")
        components = [get_tests_root(path), prefix + u_relpath]
    elif tests_structure == "side-by-side":
        reldir, filename = os.path.split(relpath)
        components = [reldir, prefix + filename]
    else:
        relpath = add_test_prefix_to_all_path_components(relpath)
        components = [get_tests_root(path), relpath]

    return os.sep.join(components)
    # }}}


def find_source_file_for_test_file(path):  # {{{
    testsroot = get_tests_root(path)
    test_prefix = vim.eval("g:test_prefix")

    rel_path = _relpath(path, testsroot)
    parts = rel_path.split(os.sep)
    parts = [_strip_prefix(p, test_prefix) for p in parts]
    sourcefile = os.sep.join(parts)

    src_root = find_source_root(path)
    tests_structure = vim.eval("g:tests_structure")
    if tests_structure == "flat":
        # A flat test structure makes it somewhat ambiguous to deduce the test
        # file for the given testfile.  For example, a test file called
        # test_foo_bar.py could belong to these four files:
        #
        # - foo/bar.py
        # - foo/bar/__init__.py
        # - foo_bar.py
        # - foo_bar/__init__.py
        #
        # The solution is to try them all and if we find a match, we use that
        # file.  In case of multiple matches, we simply use the first.

        def slashgenerator(length, select_from, select_last_from):
            if length <= 0:
                for opt in select_last_from:
                    yield [opt]
            else:
                for opt in select_from:
                    for x in slashgenerator(length - 1, select_from, \
                                     select_last_from):
                        yield [opt] + x

        def interlace(x, y):
            max_ = max(len(x), len(y))
            for i in xrange(max_):
                if i < len(x):
                    yield x[i]
                if i < len(y):
                    yield y[i]

        stripped, extension = os.path.splitext(sourcefile)
        sourcefile = None
        parts = stripped.split("_")

        intermediate_pairs = ['/', '_']
        last_pair = [extension, '/__init__' + extension]
        print intermediate_pairs, last_pair
        for slashes in slashgenerator(len(parts) - 1, intermediate_pairs, \
                               last_pair):
            guess = os.path.join(src_root, "".join(interlace(parts, slashes)))
            if os.path.isfile(guess):
                sourcefile = guess
                break

        if not sourcefile:
            raise Exception("Source file not found.")
    else:
        # For non-flat tests structures, the source file can either be the
        # source file as is (most likely), or an __init__.py file.  Try that
        # alternative if the regular sourcefile doesn't exist.
        sourcefile = os.path.join(src_root, sourcefile)
        if not os.path.isfile(sourcefile):
            filepath, extension = os.path.splitext(sourcefile)
            sourcefile = "".join([filepath, os.sep, "__init__", extension])
            if not os.path.isfile(sourcefile):
                raise Exception("Source file not found.")

    return sourcefile
    # }}}


def is_test_file(path):  # {{{
    if vim.eval('g:tests_structure') == 'side-by-side':
        # For side-by-side, test files need only to start with the
        # prefix, their location is unimportant
        prefix = vim.eval('g:test_prefix')
        _, filename = os.path.split(path)
        return filename.startswith(prefix)
    else:
        # For non-side-by-side tests, being in the test root means
        # you're a test file
        testroot = os.path.abspath(get_tests_root(path))
        path = os.path.abspath(path)
        return path.startswith(testroot)
    # }}}


def _vim_split_cmd(inverted=False):  # {{{
    invert = {'top': 'bottom', 'left': 'right',
              'right': 'left', 'bottom': 'top', 'no': 'no'}
    mapping = {'top': 'lefta', 'left': 'vert lefta',
               'right': 'vert rightb', 'bottom': 'rightb', 'no': ''}
    splitoff_direction = vim.eval("g:tests_split_window")
    if inverted:
        return mapping[invert[splitoff_direction]]
    else:
        return mapping[splitoff_direction]
    # }}}


def _open_buffer_cmd(path, opposite=False):  # {{{
    splitopts = _vim_split_cmd(opposite)
    if not splitopts:
        splitcmd = 'edit'
    elif int(vim.eval('bufexists("%s")' % path)):
        splitcmd = splitopts + ' sbuffer'
    else:
        splitcmd = splitopts + ' split'
    command = "%s %s" % (splitcmd, path)
    return command
    # }}}


def switch_to_test_file_for_source_file(path):  # {{{
    testfile = get_test_file_for_source_file(path)
    testdir = os.path.dirname(testfile)
    testfile = _relpath(testfile, '.')
    if not os.path.isfile(testfile):
        if int(vim.eval('g:confirm_test_creation')):
            # Ask the user for confirmation
            msg = 'confirm("Test file does not exist yet. Create %s now?", "&Yes\n&No")' % testfile
            if int(vim.eval(msg)) != 1:
                return

        # Create the directory up until the file (if it doesn't exist yet)
        if not os.path.exists(testdir):
            os.makedirs(testdir)

    vim.command(_open_buffer_cmd(testfile))
    # }}}


def switch_to_source_file_for_test_file(path):  # {{{
    sourcefile = find_source_file_for_test_file(path)
    relpath = _relpath(sourcefile, '.')
    vim.command(_open_buffer_cmd(relpath, opposite=True))
    # }}}


@bridged  # {{{
def switch_to_alternate_file_for_file(path):
    if is_test_file(path):
        switch_to_source_file_for_test_file(path)
    else:
        switch_to_test_file_for_source_file(path)
    # }}}


@bridged  # {{{
def run_tests_for_file(path):
    if not is_test_file(path):
        path = get_test_file_for_source_file(path)
    relpath = _relpath(path, '.')
    vim.command('call RunTestsForTestFile("%s")' % relpath)
    # }}}
