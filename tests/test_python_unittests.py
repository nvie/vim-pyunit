# Mock out the vim library
import sys
sys.path = ['tests/mocks'] + sys.path
import vim

vimvar = {}


def fake_eval(x):
    global vimvar
    return vimvar[x]

vim.eval = fake_eval
vimvar['foo'] = 'bar'

# Now start loading normally
import unittest
import os
import python_unittests as mod


# Calculate the *real* project root for this test scenario
proj_root = os.getcwd()
currfile = __file__.replace('.pyc', '.py')


class TestSomething(unittest.TestCase):

    def assertSameFile(self, x, y):
        self.assertEquals(os.path.realpath(x), os.path.realpath(y))

    # Prepare testing environment {{{

    def setUp(self):
        # Start with a fresh vim environment
        vimvar.clear()

        # Set the project defaults
        vimvar.update({
            'g:show_tests': '1',
            'g:pyunit_cmd': 'nosetests -q --with-machineout',
            'g:test_prefix': 'test_',
            'g:projroot_indicators': ['.git', 'setup.py', 'setup.cfg'],
            'g:projroot_stop_at_home_dir': '1',
            'g:tests_structure': 'follow-hierarchy',
            'g:tests_root': 'tests',
            'g:source_root': '',
            'g:tests_split_window': 'right',
        })

    def test_patch(self):
        self.assertEquals(vim.eval('g:test_prefix'), 'test_')
        self.assertEquals(vim.eval('g:show_tests'), '1')

    # }}}

    def test_is_test_file(self):  # {{{
        self.assertTrue(mod.is_test_file('tests/foo.py'))

        vimvar['g:tests_root'] = 'my_tests'
        self.assertFalse(mod.is_test_file('tests/foo.py'))

        vimvar['g:tests_structure'] = 'side-by-side'
        self.assertTrue(mod.is_test_file('src/module/test_foo.py'))
        # }}}

    def test_is_fs_root(self):  # {{{
        self.assertTrue(mod.is_fs_root('/'))
        self.assertFalse(mod.is_fs_root(''))
        self.assertTrue(mod.is_fs_root(os.path.expandvars('$HOME')))
        vimvar['g:projroot_stop_at_home_dir'] = '0'
        self.assertFalse(mod.is_fs_root(os.path.expandvars('$HOME')))
        # }}}

    def test_find_project_root(self):  # {{{
        self.assertEquals(mod.find_project_root(currfile), proj_root)
        # }}}

    def test_source_root(self):  # {{{
        self.assertEquals(mod.find_source_root(currfile),
                          proj_root + '/')
        vimvar['g:source_root'] = 'src'
        self.assertEquals(mod.find_source_root(currfile),
                          os.path.join(proj_root, 'src'))
        # }}}

    def test_vim_splitcmd(self):  # {{{
        self.assertEquals(mod._vim_split_cmd(), 'vert rightb')
        self.assertEquals(mod._vim_split_cmd(True), 'vert lefta')

        vimvar['g:tests_split_window'] = 'left'
        self.assertEquals(mod._vim_split_cmd(), 'vert lefta')
        self.assertEquals(mod._vim_split_cmd(True), 'vert rightb')

        vimvar['g:tests_split_window'] = 'top'
        self.assertEquals(mod._vim_split_cmd(), 'lefta')
        self.assertEquals(mod._vim_split_cmd(True), 'rightb')

        vimvar['g:tests_split_window'] = 'bottom'
        self.assertEquals(mod._vim_split_cmd(True), 'lefta')
        self.assertEquals(mod._vim_split_cmd(), 'rightb')
        # }}}

    def test_open_buffer(self):  # {{{
        vimvar['bufexists("foo")'] = '1'
        self.assertTrue(mod._open_buffer_cmd('foo'),
                'vert rightb sbuffer foo')

        vimvar['bufexists("foo")'] = '0'
        self.assertTrue(mod._open_buffer_cmd('foo'),
                'vert rightb split foo')

        vimvar['g:tests_split_window'] = 'no'
        self.assertTrue(mod._open_buffer_cmd('foo'),
                'edit foo')
        # }}}

    def test_get_test_file_for_normal_source_file(self):  # {{{
        self.assertSameFile(mod.get_test_file_for_source_file('foo/bar/qux.py'),
                'tests/test_foo/test_bar/test_qux.py')

        vimvar['g:tests_root'] = 'misc/mytests'
        self.assertSameFile(mod.get_test_file_for_source_file('foo/bar/qux.py'),
                'misc/mytests/test_foo/test_bar/test_qux.py')

        vimvar['g:tests_structure'] = 'flat'
        self.assertSameFile(mod.get_test_file_for_source_file('foo/bar/qux.py'),
                'misc/mytests/test_foo_bar_qux.py')

        vimvar['g:tests_structure'] = 'side-by-side'
        self.assertSameFile(mod.get_test_file_for_source_file('foo/bar/qux.py'),
                'foo/bar/test_qux.py')
        # }}}

    def test_get_test_file_for_init_source_file(self):  # {{{
        self.assertSameFile(mod.get_test_file_for_source_file('foo/bar/__init__.py'),
                'tests/test_foo/test_bar.py')

        vimvar['g:tests_root'] = 'misc/mytests'
        self.assertSameFile(mod.get_test_file_for_source_file('foo/bar/__init__.py'),
                'misc/mytests/test_foo/test_bar.py')

        vimvar['g:tests_structure'] = 'flat'
        self.assertSameFile(mod.get_test_file_for_source_file('foo/bar/__init__.py'),
                'misc/mytests/test_foo_bar.py')

        vimvar['g:tests_structure'] = 'side-by-side'
        self.assertSameFile(mod.get_test_file_for_source_file('foo/bar/__init__.py'),
                'foo/test_bar.py')
        # }}}

    def test_get_source_file_for_test_file(self):  # {{{
        self.assertRaises(Exception,
                mod.find_source_file_for_test_file, currfile)
        vimvar['g:source_root'] = 'src'
        self.assertSameFile(mod.find_source_file_for_test_file(currfile),
                os.path.realpath('src/python_unittests.py'))
        # }}}
