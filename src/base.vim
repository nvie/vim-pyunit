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
let loaded_python_unittests_ftplugin = 1

" Configuration of the test tool {{{
" Set the PyUnitCmd to whatever is your testing tool (default: nosetests)
if !exists("g:PyUnitCmd")
    let PyUnitCmd = "nosetests -q --with-machineout"
endif

" Set PyUnitShowTests to 1 if you want to show the tests (default: 1)
if !exists("g:PyUnitShowTests")       " TODO: Use this one!
    let PyUnitShowTests = 1
endif

"}}}
" Configuration for autodetecting project root {{{
" Configure what files indicate a project root
if !exists("g:ProjRootIndicators")
    let ProjRootIndicators = [ ".git", "setup.py", "setup.cfg" ]
endif

" Scan from the current working directory up until the home dir, instead of
" the filesystem root.  This has no effect on projects that reside outside the
" user's home directory.  In those cases there will be scanned up until the
" filesystem root directory.
if !exists("g:ProjRootStopAtHomeDir")
    let ProjRootStopAtHomeDir = 1
endif
" }}}
" Configuration for tests organisation {{{
" Prefix used for all path components of the test file
if !exists("g:PyUnitTestPrefix")
    " nosetests scans all files/directories starting with "test_", so this is
    " a sane default value.  There should not be a need to change this if you
    " want to use nose.
    let PyUnitTestPrefix = "test_"
endif

" Location where the source files live.  When set, this must be the relative
" directory under the project root.  For example, if you have your project
" root as follows:
" - foo/
" - bar/
" - tests/
"
" And you want the test structure:
" - tests/test_foo/
" - tests/test_bar/
"
" Then you can leave this at the default value ("").
"
" But if you have:
" - src/
"   - foo/
"   - bar/
" - tests/
"
" And you DON'T want:
" - tests/test_src/test_foo/
" - tests/test_src/test_bar/
" but:
" - tests/test_foo/
" - tests/test_bar/
"
" Then you need to set this value to "src"
if !exists("g:PyUnitSourceRoot")
    let PyUnitSourceRoot = ""
endif

" Relative location under the project root where to look for the test files.
if !exists("g:PyUnitTestsRoot")
    let PyUnitTestsRoot = "tests"
endif

" Tests structure can be one of: flat, follow-hierarchy
"let PyUnitTestsStructure = "flat"
if !exists("g:PyUnitTestsStructure")
    let PyUnitTestsStructure = "follow-hierarchy"
endif
" }}}
" Configuration for editing preferences {{{
if !exists("g:PyUnitConfirmTestCreation")
    " Set this to 0 if you want to silently create new test files
    let PyUnitConfirmTestCreation = 1
endif
if !exists("g:PyUnitTestsSplitWindow")
    " Specifies how the test window should open, relative to the source file
    " window.  Takes one of the following values: top, bottom, left, right
    let PyUnitTestsSplitWindow = "right"
endif
" }}}

python << endpython
__PYTHON_SOURCE__
endpython

fun! PyUnitRunTestsForTestFile(path) " {{{
    silent write
    call PyUnitRunNose(a:path)
endf " }}}

fun! PyUnitRunNose(path) " {{{
    " TODO: fix this hard-coded "nosetests" string!
    if !executable("nosetests")
        echoerr "File " . "nosetests" . " not found. Please install it first."
        return
    endif

    set lazyredraw   " delay redrawing
    cclose           " close any existing cwindows

    " store old grep settings (to restore later)
    let old_gfm=&grepformat
    let old_gp=&grepprg

    " write any changes before continuing
    if !&readonly
        update
    endif

    " perform the grep itself
    let &grepformat = "%f:%l: fail: %m,%f:%l: error: %m"
    if g:PyUnitSourceRoot != ""
        let &grepprg = "PYTHONPATH=".g:PyUnitSourceRoot." ".g:PyUnitCmd
    else
        let &grepprg = g:PyUnitCmd
    endif
    execute "silent! grep! ".a:path

    " restore grep settings
    let &grepformat=old_gfm
    let &grepprg=old_gp

    " open cwindow
    let has_errors=getqflist() != []
    if has_errors
        " first, open the alternate window, too
        call PyUnitSwitchToCounterpart()
        execute 'belowright copen'
        setlocal wrap
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
        let numfail = len(getqflist())
        if numfail == 1
            echon "1 test failed."
        else
            echon numfail." tests failed."
        endif
    endif
endf # }}}

fun! s:RedBar() " {{{
    hi RedBar ctermfg=white ctermbg=red guibg=red
    echohl RedBar
    echon repeat(" ", &columns - 1)
    echohl
endf " }}}

fun! s:GreenBar() " {{{
    hi GreenBar ctermfg=white ctermbg=green guibg=green
    echohl GreenBar
    echon repeat(" ", &columns - 1)
    echohl
endf " }}}

fun! PyUnitSwitchToCounterpart() " {{{
    call PyUnitSwitchToCounterpartOfFile(@%)
endf " }}}

fun! PyUnitRunTests() " {{{
    call PyUnitRunTestsForFile(@%)
endf " }}}

fun! PyUnitRunAllTests() " {{{
    silent w
    call PyUnitRunNose('')
endf " }}}

" Keyboard mappings {{{

" Add mappings, unless the user didn't want this.
" The default mapping is registered under to <F8> by default, unless the user
" remapped it already (or a mapping exists already for <F8>)
if !exists("no_plugin_maps") && !exists("no_pyunit_maps")
    if !hasmapto('PyUnitRunTests(')
        noremap <silent> <F8> :call PyUnitRunTests()<CR>
        noremap! <silent> <F8> <Esc>:call PyUnitRunTests()<CR>
    endif
    if !hasmapto('PyUnitRunAllTests(')
        noremap <silent> <S-F8> :call PyUnitRunAllTests()<CR>
        noremap! <silent> <S-F8> <Esc>:call PyUnitRunAllTests()<CR>
    endif
    if !hasmapto('PyUnitSwitchToCounterpart(')
        noremap <silent> <F9> :call PyUnitSwitchToCounterpart()<CR>
        noremap! <silent> <F9> <Esc>:call PyUnitSwitchToCounterpart()<CR>
    endif
endif

" }}}
