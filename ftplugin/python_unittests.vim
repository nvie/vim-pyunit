"
" Python filetype plugin for unit testing (currently with nose)
" Language:     Python (ft=python)
" Maintainer:   Vincent Driessen <vincent@datafox.nl>
" Version:      Vim 7 (may work with lower Vim versions, but not tested)
" URL:          http://github.com/nvie/vim-pyunit
"
" Very inspired by Gary Bernhart's work:
"     http://bitbucket.org/garybernhardt/dotfiles/src/tip/.vimrc
"
" Based on Mike Crute's Vim plugin:
"     http://code.crute.org/mcrute_dotfiles/file/a19ddffcabe6/.vim/plugin/python_testing.vim
"

" Only do this when not done yet for this buffer
if exists("g:loaded_python_unittests_ftplugin")
    finish
endif
let g:loaded_python_unittests_ftplugin = 1

" Configuration of the test tool {{{
" Set the pyunit_cmd to whatever is your testing tool (default: nosetests)
if !exists("g:pyunit_cmd")
    let g:pyunit_cmd = "nosetests -q --with-machineout"
endif

" Set show_tests to 1 if you want to show the tests (default: 1)
if !exists("g:show_tests")       " TODO: Use this one!
    let g:show_tests = 1
endif

let &grepformat = "%f:%l: fail: %m,%f:%l: error: %m"
let &grepprg = g:pyunit_cmd
"}}}
" Configuration for autodetecting project root {{{
" Configure what files indicate a project root
if !exists("g:projroot_indicators")
    let g:projroot_indicators = [ ".git", ".lvimrc", "setup.py", "setup.cfg" ]
endif

" Scan from the current working directory up until the home dir, instead of
" the filesystem root.  This has no effect on projects that reside outside the
" user's home directory.  In those cases there will be scanned up until the
" filesystem root directory.
if !exists("g:projroot_stop_at_home_dir")
    let g:projroot_stop_at_home_dir = 1
endif
" }}}
" Configuration for tests organisation {{{
" Prefix used for all path components of the test file
if !exists("g:test_prefix")
    " nosetests scans all files/directories starting with "test_", so this is
    " a sane default value.  There should not be a need to change this.
    let g:test_prefix = "test_"
endif

" Relative location from the project root (the project root is autodetected,
" see g:projroot_indicators)
if !exists("g:tests_location")
    let g:tests_location = "tests"
endif

" Tests structure can be one of: flat, follow-hierarchy
"let g:tests_structure = "flat"
if !exists("g:tests_structure")
    let g:tests_structure = "follow-hierarchy"
endif
" }}}

python << endpython
import vim
import sys
import os
import os.path
from vim_bridge import bridged

def is_home_dir(path): # {{{
    return os.path.realpath(path) == os.path.expandvars("$HOME")
    # }}}

def is_fs_root(path): # {{{
    return os.path.realpath(path) == "/" or \
           (vim.eval("g:projroot_stop_at_home_dir") and is_home_dir(path))
    # }}}

@bridged # {{{
def find_project_root(path):
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

def _strip_prefix(s, prefix): # {{{
    if prefix != "" and s.startswith(prefix):
        return s[len(prefix):]
    else:
        return s
    # }}}

def _strip_suffix(s, suffix, replace_by = ''): # {{{
    if suffix != "" and s.endswith(suffix):
        return s[:-len(suffix)] + replace_by
    else:
        return s
    # }}}

def _relpath(path, start='.'): # {{{
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

@bridged # {{{
def get_relative_path_in_project(path):
    root = find_project_root(path)
    return _relpath(path, root)
    # }}}

@bridged # {{{
def get_tests_root(path):
    loc = vim.eval("g:tests_location")
    return os.sep.join([find_project_root(path), loc])
    # }}}

@bridged # {{{
def add_test_prefix_to_all_path_components(path):
    prefix = vim.eval("g:test_prefix")
    components = path.split(os.sep)
    return os.sep.join([s and prefix + s or s for s in components])
    # }}}

@bridged # {{{
def get_test_file_for_source_file(path):
    prefix = vim.eval("g:test_prefix")
    testsroot = get_tests_root(path)

    relpath = get_relative_path_in_project(path)
    relpath = _strip_suffix(relpath, os.sep + '__init__.py', '.py')
    u_relpath = relpath.replace("/", "_")

    if vim.eval("g:tests_structure") == "flat":
        components = [testsroot, prefix + u_relpath]
    else:
        relpath = add_test_prefix_to_all_path_components(relpath)
        components = [testsroot, relpath]

    return os.sep.join(components)
    # }}}

@bridged # {{{
def find_source_file_for_test_file(path):
    testsroot = get_tests_root(path)
    test_prefix = vim.eval("g:test_prefix")

    rel_path = _relpath(path, testsroot)
    parts = rel_path.split(os.sep)
    parts = [_strip_prefix(p, test_prefix) for p in parts]
    sourcefile = os.sep.join(parts)

    if vim.eval("g:tests_structure") == "flat":
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
                    for x in slashgenerator(length - 1, select_from, select_last_from):
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

        intermediate_pairs = ['/','_']
        last_pair = [extension, '/__init__' + extension]
        print intermediate_pairs, last_pair
        for slashes in slashgenerator(len(parts)-1, intermediate_pairs, last_pair):
            guess = "".join(interlace(parts, slashes))
            if os.path.isfile(guess):
                sourcefile = guess
                break

        if not sourcefile:
            raise Exception("Source file not found.")
    else:
        # For non-flat tests structures, the source file can either be the
        # source file as is (most likely), or an __init__.py file.  Try that
        # alternative if the regular sourcefile doesn't exist.
        if not os.path.isfile(sourcefile):
            filepath, extension = os.path.splitext(sourcefile)
            sourcefile = "".join([filepath, os.sep, "__init__", extension])
            if not os.path.isfile(sourcefile):
                raise Exception("Source file not found.")

    return sourcefile
    # }}}

@bridged # {{{
def is_test_file(path):
    testroot = os.path.abspath(get_tests_root(path))
    path = os.path.abspath(path)
    return path.startswith(testroot)
    # }}}

def _open_buffer(path, splitopts): # {{{
    path = _relpath(path, ".")
    if int(vim.eval('bufexists("%s")' % path)):
        splitcmd = 'sbuffer'
    else:
        splitcmd = 'split'
    command = "%s %s %s" % (splitopts, splitcmd, path)
    vim.command(command)
    # }}}

@bridged # {{{
def switch_to_test_file_for_source_file(path):
    testfile = get_test_file_for_source_file(path)
    testdir = os.path.dirname(testfile)
    if not os.path.isfile(testfile):
        # Create the directory up until the file (if it doesn't exist yet)
        if not os.path.exists(testdir):
            os.makedirs(testdir)

    _open_buffer(testfile, 'vert rightb')
    # }}}

@bridged # {{{
def switch_to_source_file_for_test_file(path):
    sourcefile = find_source_file_for_test_file(path)
    _open_buffer(sourcefile, 'vert lefta')
    # }}}

# === Running tests (def ) {{{1 ================================================

@bridged # {{{
def run_tests_for_file(path):
    if not is_test_file(path):
        path = get_test_file_for_source_file(path)
    relpath = _relpath(path, '.')
    vim.command('call RunTestsForTestFile("%s")' % relpath)
    # }}}

# }}}

endpython

fun! RunTestsForTestFile(path)
    silent! echo
    exec 'silent! echo -e "\033[1;36mRunning tests for ' . a:path . '\033[0m"'
    silent write
    call RunNose(a:path)
endf

fun! RunNose(path)
    " TODO: fix this hard-coded "nosetests" string!
    if !executable("nosetests")
        echoerr "File " . "nosetests" . " not found. Please install it first."
        return
    endif

    set lazyredraw   " delay redrawing
    cclose           " close any existing cwindows

    " store old grep settings (to restore later)
    let l:old_gfm=&grepformat
    let l:old_gp=&grepprg

    " write any changes before continuing
    if !&readonly
        update
    endif

    " perform the grep itself
    let &grepformat = "%f:%l: fail: %m,%f:%l: error: %m"
    let &grepprg = g:pyunit_cmd
    execute "silent! grep! ".a:path

    " restore grep settings
    let &grepformat=l:old_gfm
    let &grepprg=l:old_gp

    " open cwindow
    let has_errors=getqflist() != []
    if has_errors
        " first, open the alternate window, too
        call SwitchToAlternateFileForCurrentFile()
        execute 'belowright copen'
        nnoremap <buffer> <silent> c :cclose<CR>
        nnoremap <buffer> <silent> q :cclose<CR>
    endif

    set nolazyredraw
    redraw!

    if !has_errors
        " Show OK status
        call s:GreenBar()
        echo ""
        hi Green ctermfg=green
        echohl Green
        echon "All tests passed."
        echohl
    else
        call s:RedBar()
        echo ""
        hi Red ctermfg=red
        echohl Red
        let l:numfail = len(getqflist())
        if l:numfail == 1
            echon "1 test failed."
        else
            echon l:numfail." tests failed."
        endif
        silent cc!
    endif
endf

fun! SwitchToAlternateFileForCurrentFile()
    if IsTestFile(@%)
        call SwitchToSourceFileForTestFile(@%)
    else
        call SwitchToTestFileForSourceFile(@%)
    endif
endf

" -------------------------------------------------------------------------------
" ----------------- BELOW HERE IS GARY'S CODE -----------------------------------
" -------------------------------------------------------------------------------

" Unit Test Functions {{{
fun! s:RedBar()
    hi RedBar ctermfg=white ctermbg=red guibg=red
    echohl RedBar
    echon repeat(" ", &columns - 1)
    echohl
endf

fun! s:GreenBar()
    hi GreenBar ctermfg=white ctermbg=green guibg=green
    echohl GreenBar
    echon repeat(" ", &columns - 1)
    echohl
endf
" }}}

" {{{ Testing Support 

fun! RunTests(target, args)
    silent ! echo
    exec 'silent ! echo -e "\033[1;36mRunning tests in ' . a:target . '\033[0m"'
    set grepprg=nosetests
    silent w
    exec "grep! " . a:target . " " . a:args
endf

fun! RunTestsForCurrentFile()
    call RunTestsForFile(@%)
endf

fun! RunAllTests(args)
    silent ! echo
    silent ! echo -e "\033[1;36mRunning all unit tests\033[0m"
    set grepprg=nosetests
    silent w
    exec "grep! tests.unit " . a:args
endf

fun! JumpToError()
    if getqflist() != []
        for error in getqflist()
            if error['valid']
                break
            endif
        endfor
        let error_message = substitute(error['text'], '^ *', '', 'g')
        " silent cc!
        let error_buffer = error['bufnr']
        if g:show_tests == 1
            exec ":vs"
            exec ":buffer " . error_buffer
        endif
        exec "normal ".error['lnum']."G"
        call s:RedBar()
        echo error_message
    else
        call s:GreenBar()
        echo "All tests passed"
    endif
endf

fun! JumpToTestsForClass()
    exec 'e ' . TestFileForCurrentClass()
endf
" }}}

" Keyboard mappings {{{
" nnoremap <leader>m :call RunTestsForFile('-q --with-machineout')<cr>:redraw<cr>:call JumpToError()<cr>
" nnoremap <leader>M :call RunTestsForFile('')<cr>
" nnoremap <leader>a :call RunAllTests('-q --with-machineout')<cr>:redraw<cr>:call JumpToError()<cr>
" nnoremap <leader>A :call RunAllTests('')<cr>
" nnoremap <leader>t :call JumpToTestsForClass()<cr>
" nnoremap <leader><leader> <c-^>
" }}}

" --------------------------------------------------------------------------------------
" ------------------------------- HERE's MINE AGAIN ------------------------------------
" --------------------------------------------------------------------------------------

noremap <F8> :call RunTestsForCurrentFile()<CR>
noremap! <F8> <Esc>:call RunTestsForCurrentFile()<CR>
noremap <F9> :call SwitchToAlternateFileForCurrentFile()<CR>
noremap! <F9> <Esc>:call SwitchToAlternateFileForCurrentFile()<CR>

" Add mappings, unless the user didn't want this.
" The default mapping is registered under to <F8> by default, unless the user
" remapped it already (or a mapping exists already for <F8>)
if !exists("no_plugin_maps") && !exists("no_pyunit_maps")
    "if !hasmapto('RunTestsForCurrentFile()')
    "endif
endif
