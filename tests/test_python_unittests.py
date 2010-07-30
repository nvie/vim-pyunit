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


class TestSomething(unittest.TestCase):

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
        self.assertEquals(mod.find_project_root(__file__), proj_root)
        # }}}

    def test_source_root(self):  # {{{
        self.assertEquals(mod.find_source_root(__file__),
                          proj_root+'/')
        vimvar['g:source_root'] = 'src'
        self.assertEquals(mod.find_source_root(__file__),
                          os.path.join(proj_root, 'src'))
        # }}}

    def test_(self):  # {{{
        self.assertEquals(mod.find_source_root(__file__),
                          proj_root+'/')
        vimvar['g:source_root'] = 'src'
        self.assertEquals(mod.find_source_root(__file__),
                          os.path.join(proj_root, 'src'))
        # }}}
