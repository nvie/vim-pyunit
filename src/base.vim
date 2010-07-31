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
" Set the pyunit_cmd to whatever is your testing tool (default: nosetests)
if !exists("g:pyunit_cmd")
    let pyunit_cmd = "nosetests -q --with-machineout"
endif

" Set show_tests to 1 if you want to show the tests (default: 1)
if !exists("g:show_tests")       " TODO: Use this one!
    let show_tests = 1
endif

let &grepformat = "%f:%l: fail: %m,%f:%l: error: %m"
let &grepprg = g:pyunit_cmd
"}}}
" Configuration for autodetecting project root {{{
" Configure what files indicate a project root
if !exists("g:projroot_indicators")
    let projroot_indicators = [ ".git", "setup.py", "setup.cfg" ]
endif

" Scan from the current working directory up until the home dir, instead of
" the filesystem root.  This has no effect on projects that reside outside the
" user's home directory.  In those cases there will be scanned up until the
" filesystem root directory.
if !exists("g:projroot_stop_at_home_dir")
    let projroot_stop_at_home_dir = 1
endif
" }}}
" Configuration for tests organisation {{{
" Prefix used for all path components of the test file
if !exists("g:test_prefix")
    " nosetests scans all files/directories starting with "test_", so this is
    " a sane default value.  There should not be a need to change this if you
    " want to use nose.
    let test_prefix = "test_"
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
if !exists("g:source_root")
    let source_root = ""
endif

" Relative location under the project root where to look for the test files.
" Not used when tests_structure is "side-by-side".
if !exists("g:tests_root")
    let tests_root = "tests"
endif

" Tests structure can be one of: flat, follow-hierarchy, side-by-side
"let tests_structure = "flat"
if !exists("g:tests_structure")
    let tests_structure = "follow-hierarchy"
endif
" }}}
" Configuration for editing preferences {{{
if !exists("g:tests_split_window")
    " Specifies how the test window should open, relative to the source file
    " window.  Takes one of the following values: top, bottom, left, right
    let tests_split_window = "right"
endif
" }}}

python << endpython
__PYTHON_SOURCE__
endpython

fun! RunTestsForTestFile(path)
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
    let old_gfm=&grepformat
    let old_gp=&grepprg

    " write any changes before continuing
    if !&readonly
        update
    endif

    " perform the grep itself
    let &grepformat = "%f:%l: fail: %m,%f:%l: error: %m"
    let &grepprg = g:pyunit_cmd
    execute "silent! grep! ".a:path

    " restore grep settings
    let &grepformat=old_gfm
    let &grepprg=old_gp

    " open cwindow
    let has_errors=getqflist() != []
    if has_errors
        " first, open the alternate window, too
        call SwitchToAlternateFileForCurrentFile()
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
        silent cc!
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

fun! SwitchToAlternateFileForCurrentFile()
    call SwitchToAlternateFileForFile(@%)
endf

fun! RunTestsForCurrentFile()
    call RunTestsForFile(@%)
endf

fun! RunAllTests()
    silent w
    call RunNose('')
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
" }}}

" Keyboard mappings {{{
" nnoremap <leader>m :call RunTestsForFile('-q --with-machineout')<cr>:redraw<cr>:call JumpToError()<cr>
" nnoremap <leader>M :call RunTestsForFile('')<cr>
" nnoremap <leader>a :call RunAllTests('-q --with-machineout')<cr>:redraw<cr>:call JumpToError()<cr>
" nnoremap <leader>A :call RunAllTests('')<cr>
" }}}

" --------------------------------------------------------------------------------------
" ------------------------------- HERE's MINE AGAIN ------------------------------------
" --------------------------------------------------------------------------------------

noremap <F8> :call RunTestsForCurrentFile()<CR>
noremap! <F8> <Esc>:call RunTestsForCurrentFile()<CR>
noremap <S-F8> :call RunAllTests()<CR>
noremap! <S-F8> <Esc>:call RunAllTests()<CR>
noremap <F9> :call SwitchToAlternateFileForCurrentFile()<CR>
noremap! <F9> <Esc>:call SwitchToAlternateFileForCurrentFile()<CR>

" Add mappings, unless the user didn't want this.
" The default mapping is registered under to <F8> by default, unless the user
" remapped it already (or a mapping exists already for <F8>)
if !exists("no_plugin_maps") && !exists("no_pyunit_maps")
    "if !hasmapto('RunTestsForCurrentFile()')
    "endif
endif
