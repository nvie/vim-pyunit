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
            'g:PyUnitShowTests': '1',
            'g:PyUnitCmd': 'nosetests -q --with-machineout',
            'g:PyUnitTestPrefix': 'test_',
            'g:ProjRootIndicators': ['.git', 'setup.py', 'setup.cfg'],
            'g:ProjRootStopAtHomeDir': '1',
            'g:PyUnitTestsStructure': 'follow-hierarchy',
            'g:PyUnitTestsRoot': 'tests',
            'g:PyUnitSourceRoot': '',
            'g:PyUnitTestsSplitWindow': 'right',
        })

    def test_patch(self):
        self.assertEquals(vim.eval('g:PyUnitTestPrefix'), 'test_')
        self.assertEquals(vim.eval('g:PyUnitShowTests'), '1')



    def test_is_fs_root(self):
        self.assertTrue(mod.is_fs_root('/'))
        self.assertFalse(mod.is_fs_root(''))
        self.assertTrue(mod.is_fs_root(os.path.expandvars('$HOME')))
        vimvar['g:ProjRootStopAtHomeDir'] = '0'
        self.assertFalse(mod.is_fs_root(os.path.expandvars('$HOME')))

    def test_find_project_root(self):
        self.assertEquals(mod.find_project_root(currfile), proj_root)

    def test_source_root(self):
        self.assertEquals(mod.find_source_root(currfile),
                          proj_root + '/')
        vimvar['g:PyUnitSourceRoot'] = 'src'
        self.assertEquals(mod.find_source_root(currfile),
                          os.path.join(proj_root, 'src'))

        vimvar['g:PyUnitSourceRoot'] = 'alt-src'
        self.assertEquals(mod.find_source_root(currfile),
                          os.path.join(proj_root, 'alt-src'))

        vimvar['g:PyUnitSourceRoot'] = ''
        self.assertEquals(mod.find_source_root(currfile),
                          os.path.join(proj_root, ''))


    def test_relpath(self):
        # Nice and simple
        self.assertEquals(
                mod._relpath('/tmp/foo/bar', '/tmp', try_stdlib=False),
                'foo/bar')
        self.assertEquals(
                mod._relpath('/etc/passwd', '/', try_stdlib=False),
                'etc/passwd')

        # Walking backward
        self.assertEquals(
                mod._relpath('.././foo/bar.py', '.', try_stdlib=False),
                '../foo/bar.py')
        self.assertEquals(
                mod._relpath('/a/b', '/c', try_stdlib=False),
                '../a/b')
        self.assertEquals(
                mod._relpath('/a/b/c', '/d/e', try_stdlib=False),
                '../../a/b/c')
        self.assertEquals(
                mod._relpath('/', '/a/b', try_stdlib=False),
                '../../')

        # Directory signs shouldn't matter
        self.assertEquals(
                mod._relpath('foo/', 'foo', try_stdlib=False), '.')
        self.assertEquals(
                mod._relpath('foo', 'foo/', try_stdlib=False), '.')
        self.assertEquals(
                mod._relpath('foo', 'foo', try_stdlib=False), '.')


    def test_is_test_file(self):
        self.assertTrue(mod.is_test_file('tests/foo.py'))

        vimvar['g:PyUnitTestsRoot'] = 'my_tests'
        self.assertFalse(mod.is_test_file('tests/foo.py'))

    def test_source_root_for_non_source_file(self):
        self.assertRaises(Exception,
                mod.find_source_root, '/tmp/foo.py')

    def test_get_test_file_for_normal_source_file(self):
        self.assertSameFile(
                mod.get_test_file_for_source_file('foo/bar/qux.py'),
                'tests/test_foo/test_bar/test_qux.py')

        vimvar['g:PyUnitTestsRoot'] = 'misc/mytests'
        self.assertSameFile(
                mod.get_test_file_for_source_file('foo/bar/qux.py'),
                'misc/mytests/test_foo/test_bar/test_qux.py')

        vimvar['g:PyUnitTestsStructure'] = 'flat'
        self.assertSameFile(
                mod.get_test_file_for_source_file('foo/bar/qux.py'),
                'misc/mytests/test_foo_bar_qux.py')

    def test_get_test_file_for_init_source_file(self):
        self.assertSameFile(
                mod.get_test_file_for_source_file('foo/bar/__init__.py'),
                'tests/test_foo/test_bar.py')

        vimvar['g:PyUnitTestsRoot'] = 'misc/mytests'
        self.assertSameFile(
                mod.get_test_file_for_source_file('foo/bar/__init__.py'),
                'misc/mytests/test_foo/test_bar.py')

        vimvar['g:PyUnitTestsStructure'] = 'flat'
        self.assertSameFile(
                mod.get_test_file_for_source_file('foo/bar/__init__.py'),
                'misc/mytests/test_foo_bar.py')

    def test_get_source_file_for_test_file(self):
        self.assertRaises(Exception,
                mod.find_source_file_for_test_file, currfile)

        vimvar['g:PyUnitSourceRoot'] = 'src'
        self.assertSameFile(
                mod.find_source_file_for_test_file('tests/test_python_unittests.py'),
                os.path.realpath('src/python_unittests.py'))


    def test_vim_split_cmd(self):
        self.assertEquals(mod._vim_split_cmd(), 'vert rightb')
        self.assertEquals(mod._vim_split_cmd(True), 'vert lefta')

        vimvar['g:PyUnitTestsSplitWindow'] = 'left'
        self.assertEquals(mod._vim_split_cmd(), 'vert lefta')
        self.assertEquals(mod._vim_split_cmd(True), 'vert rightb')

        vimvar['g:PyUnitTestsSplitWindow'] = 'top'
        self.assertEquals(mod._vim_split_cmd(), 'lefta')
        self.assertEquals(mod._vim_split_cmd(True), 'rightb')

        vimvar['g:PyUnitTestsSplitWindow'] = 'bottom'
        self.assertEquals(mod._vim_split_cmd(True), 'lefta')
        self.assertEquals(mod._vim_split_cmd(), 'rightb')

    def test_open_buffer_cmd(self):
        vimvar['bufexists("foo")'] = '1'
        self.assertEquals(mod._open_buffer_cmd('foo'),
                'vert rightb sbuffer foo')
        self.assertEquals(mod._open_buffer_cmd('foo', opposite=True),
                'vert lefta sbuffer foo')

        vimvar['bufexists("foo")'] = '0'
        self.assertEquals(mod._open_buffer_cmd('foo'),
                'vert rightb split foo')

        vimvar['g:PyUnitTestsSplitWindow'] = 'no'
        self.assertEquals(mod._open_buffer_cmd('foo'),
                'edit foo')
