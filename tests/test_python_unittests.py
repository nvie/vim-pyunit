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
# I should probably mock this out, but for the current state of affairs, this is
# too much overkill
proj_root = os.getcwd()
currfile = __file__.replace('.pyc', '.py')


def setUpVimEnvironment():
    vimvar.clear()
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

class FileAwareTestCase(unittest.TestCase):
    def assertSameFile(self, x, y):
        self.assertEquals(os.path.realpath(x), os.path.realpath(y))


class TestTestLayout(FileAwareTestCase):
    def testBreakDownSimple(self):
        layout = mod.BaseTestLayout()
        self.assertEquals(layout.break_down('foo.py'), ['foo'])
        self.assertEquals(layout.break_down('foo/bar.py'), ['foo', 'bar'])
        self.assertEquals(layout.break_down('foo/bar/baz.py'), ['foo', 'bar', 'baz'])

    def testBreakDownWithUnderUnderInits(self):
        layout = mod.BaseTestLayout()
        self.assertEquals(layout.break_down('__init__.py'), [])
        self.assertEquals(layout.break_down('foo/__init__.py'), ['foo'])
        self.assertEquals(layout.break_down('foo/bar/baz/__init__.py'), ['foo', 'bar', 'baz'])

    def testGlueSimple(self):
        layout = mod.BaseTestLayout()
        self.assertEquals(layout.glue_parts(['foo']), 'foo.py')
        self.assertEquals(layout.glue_parts(['foo', 'bar', 'baz']), 'foo/bar/baz.py')
        self.assertRaises(IndexError, layout.glue_parts, [])

    def testGlueWithUnderUnderInits(self):
        layout = mod.BaseTestLayout()
        self.assertEquals(layout.glue_parts(['foo'], True), 'foo/__init__.py')
        self.assertEquals(layout.glue_parts(['foo', 'bar', 'baz'], True), 'foo/bar/baz/__init__.py')
        self.assertEquals(layout.glue_parts([], True), '__init__.py')

    def testRelatize(self):
        layout = mod.BaseTestLayout()
        self.assertEquals(layout.relatize("%s/foo/bar.py" % proj_root), "foo/bar.py")
        self.assertEquals(layout.relatize("foo/bar.py"), "foo/bar.py")

    def testAbsolutify(self):
        layout = mod.BaseTestLayout()
        self.assertEquals(layout.absolutify("foo/bar.py"), "%s/foo/bar.py" % proj_root)
        self.assertEquals(layout.absolutify("/tmp/foo/bar.py"), "/tmp/foo/bar.py")


class TestSideBySideLayout(FileAwareTestCase):
    def setUp(self):
        setUpVimEnvironment()

    def testDetectTestFile(self):
        vimvar['g:PyUnitSourceRoot'] = 'src'
        layout = mod.SideBySideLayout()
        self.assertTrue(layout.is_test_file('test_foo.py'))
        self.assertTrue(layout.is_test_file('foo/test_bar.py'))
        self.assertTrue(layout.is_test_file('tests/foo/test_bar.py'))
        self.assertTrue(layout.is_test_file('test_foo/test_bar.py'))
        self.assertFalse(layout.is_test_file('foo.py'))
        self.assertFalse(layout.is_test_file('src/foo.py'))
        self.assertFalse(layout.is_test_file('src/foo/bar.py'))

    def testDetectTestFileWithAlternatePrefix(self):
        vimvar['g:PyUnitTestPrefix'] = '_'
        vimvar['g:PyUnitSourceRoot'] = 'src'
        layout = mod.SideBySideLayout()
        self.assertTrue(layout.is_test_file('_foo.py'))
        self.assertTrue(layout.is_test_file('foo/_bar.py'))
        self.assertTrue(layout.is_test_file('tests/foo/_bar.py'))
        self.assertTrue(layout.is_test_file('test_foo/_bar.py'))
        self.assertFalse(layout.is_test_file('foo.py'))
        self.assertFalse(layout.is_test_file('src/foo.py'))
        self.assertFalse(layout.is_test_file('src/foo/bar.py'))

    def testDetectAbsoluteTestFile(self):
        vimvar['g:PyUnitTestPrefix'] = '_'
        vimvar['g:PyUnitSourceRoot'] = 'src'
        absdir = os.path.realpath(proj_root)
        layout = mod.SideBySideLayout()
        self.assertTrue(layout.is_test_file('%s/_foo.py' % absdir))
        self.assertTrue(layout.is_test_file('%s/foo/_bar.py' % absdir))
        self.assertTrue(layout.is_test_file('%s/tests/foo/_bar.py' % absdir))
        self.assertTrue(layout.is_test_file('%s/test_foo/_bar.py' % absdir))
        self.assertFalse(layout.is_test_file('%s/foo.py' % absdir))
        self.assertFalse(layout.is_test_file('%s/src/foo.py' % absdir))
        self.assertFalse(layout.is_test_file('%s/src/foo/bar.py' % absdir))

    def testSourceToTest(self):
        vimvar['g:PyUnitSourceRoot'] = 'src'
        layout = mod.SideBySideLayout()
        self.assertEquals(layout.get_test_file('src/foo.py'), 'src/test_foo.py')
        self.assertEquals(layout.get_test_file('src/bar.py'), 'src/test_bar.py')
        self.assertEquals(layout.get_test_file('src/bar/baz.py'), 'src/bar/test_baz.py')
        self.assertEquals(layout.get_test_file('foo.py'), 'test_foo.py')

    def testSourceToTestWithAlternatePrefix(self):
        vimvar['g:PyUnitTestPrefix'] = '_'
        vimvar['g:PyUnitSourceRoot'] = 'src'
        layout = mod.SideBySideLayout()
        self.assertEquals(layout.get_test_file('src/foo.py'), 'src/_foo.py')
        self.assertEquals(layout.get_test_file('src/bar.py'), 'src/_bar.py')
        self.assertEquals(layout.get_test_file('src/bar/baz.py'), 'src/bar/_baz.py')
        self.assertEquals(layout.get_test_file('foo.py'), '_foo.py')

    def testTestToSource(self):
        vimvar['g:PyUnitSourceRoot'] = 'src'
        layout = mod.SideBySideLayout()
        self.assertEquals(layout.get_source_candidates('src/test_foo.py'), ['src/foo.py'])
        self.assertEquals(layout.get_source_candidates('src/test_bar.py'), ['src/bar.py'])
        self.assertEquals(layout.get_source_candidates('src/bar/test_baz.py'), ['src/bar/baz.py'])
        self.assertEquals(layout.get_source_candidates('test_foo.py'), ['foo.py'])

    def testTestToSourceWithAlternatePrefix(self):
        vimvar['g:PyUnitTestPrefix'] = '_'
        vimvar['g:PyUnitSourceRoot'] = 'src'
        layout = mod.SideBySideLayout()
        self.assertEquals(layout.get_source_candidates('src/_foo.py'), ['src/foo.py'])
        self.assertEquals(layout.get_source_candidates('src/_bar.py'), ['src/bar.py'])
        self.assertEquals(layout.get_source_candidates('src/bar/_baz.py'), ['src/bar/baz.py'])
        self.assertEquals(layout.get_source_candidates('_foo.py'), ['foo.py'])


class TestFlatLayout(FileAwareTestCase):
    def setUp(self):
        setUpVimEnvironment()

    def testDetectTestFile(self):
        vimvar['g:PyUnitSourceRoot'] = 'src'
        layout = mod.FlatLayout()
        self.assertTrue(layout.is_test_file('tests/test_foo.py'))
        self.assertTrue(layout.is_test_file('tests/test_foo_bar.py'))
        self.assertTrue(layout.is_test_file('tests/test_foo_bar_baz.py'))
        self.assertFalse(layout.is_test_file('tests/test_foo/test_bar.py'))
        self.assertFalse(layout.is_test_file('foo.py'))
        self.assertFalse(layout.is_test_file('test_foo/test_bar.py'))
        self.assertFalse(layout.is_test_file('tests/foo/test_bar.py'))
        self.assertFalse(layout.is_test_file('src/foo.py'))
        self.assertFalse(layout.is_test_file('src/foo/bar.py'))

    def testDetectTestFileWithAlternatePrefix(self):
        vimvar['g:PyUnitTestPrefix'] = '_'
        vimvar['g:PyUnitSourceRoot'] = 'src'
        vimvar['g:PyUnitTestsRoots'] = 'tests'
        layout = mod.FlatLayout()
        self.assertTrue(layout.is_test_file('tests/_foo.py'))
        self.assertTrue(layout.is_test_file('tests/_foo_bar.py'))
        self.assertTrue(layout.is_test_file('tests/_foo_bar_baz.py'))
        self.assertFalse(layout.is_test_file('tests/_foo/_bar.py'))
        self.assertFalse(layout.is_test_file('foo.py'))
        self.assertFalse(layout.is_test_file('_foo/_bar.py'))
        self.assertFalse(layout.is_test_file('tests/foo/_bar.py'))
        self.assertFalse(layout.is_test_file('src/foo.py'))
        self.assertFalse(layout.is_test_file('src/foo/bar.py'))

    def testDetectAbsoluteTestFile(self):
        vimvar['g:PyUnitTestPrefix'] = '_'
        vimvar['g:PyUnitSourceRoot'] = 'src'
        vimvar['g:PyUnitTestsRoots'] = 'tests'
        absdir = os.path.realpath(proj_root)
        layout = mod.FlatLayout()
        self.assertTrue(layout.is_test_file('%s/tests/_foo.py' % absdir))
        self.assertTrue(layout.is_test_file('%s/tests/_foo_bar.py' % absdir))
        self.assertFalse(layout.is_test_file('%s/tests/_foo/_bar.py' % absdir))
        self.assertFalse(layout.is_test_file('%s/foo.py' % absdir))
        self.assertFalse(layout.is_test_file('%s/_foo/_bar.py' % absdir))
        self.assertFalse(layout.is_test_file('%s/tests/foo/_bar.py' % absdir))
        self.assertFalse(layout.is_test_file('%s/src/foo.py' % absdir))
        self.assertFalse(layout.is_test_file('%s/src/foo/bar.py' % absdir))

    def testSourceToTestFailsForNonSourceFiles(self):
        vimvar['g:PyUnitSourceRoot'] = 'src'
        layout = mod.FlatLayout()
        self.assertRaises(RuntimeError, layout.get_test_file, 'nonsrc/foo.py')
        self.assertRaises(RuntimeError, layout.get_test_file, 'foo.py')
        #self.assertRaises(RuntimeError, layout.get_test_file, 'src.py')

    def testSourceToTest(self):
        vimvar['g:PyUnitSourceRoot'] = 'src'
        layout = mod.FlatLayout()
        self.assertEquals(layout.get_test_file('src/foo.py'), 'tests/test_foo.py')
        self.assertEquals(layout.get_test_file('src/bar.py'), 'tests/test_bar.py')
        self.assertEquals(layout.get_test_file('src/bar/baz.py'), 'tests/test_bar_baz.py')

    def testSourceToTestWithAlternatePrefix(self):
        vimvar['g:PyUnitTestPrefix'] = '_'
        vimvar['g:PyUnitSourceRoot'] = 'src'
        layout = mod.FlatLayout()
        self.assertEquals(layout.get_test_file('src/foo.py'), 'tests/_foo.py')
        self.assertEquals(layout.get_test_file('src/bar.py'), 'tests/_bar.py')
        self.assertEquals(layout.get_test_file('src/bar/baz.py'), 'tests/_bar_baz.py')

    def testTestToSource(self):
        vimvar['g:PyUnitSourceRoot'] = 'src'
        layout = mod.FlatLayout()
        self.assertEquals(layout.get_source_candidates('tests/test_foo.py'), ['src/foo.py', 'src/foo/__init__.py'])
        self.assertEquals(layout.get_source_candidates('tests/test_bar.py'), ['src/bar.py', 'src/bar/__init__.py'])
        self.assertEquals(layout.get_source_candidates('tests/test_foo_bar.py'), ['src/foo/bar.py', 'src/foo/bar/__init__.py'])
        self.assertRaises(RuntimeError, layout.get_source_candidates, 'tests/foo/test_bar.py')
        self.assertRaises(RuntimeError, layout.get_source_candidates, 'test_foo.py')

    def testTestToSourceWithAlternatePrefix(self):
        vimvar['g:PyUnitSourceRoot'] = 'src'
        vimvar['g:PyUnitTestPrefix'] = '_'
        layout = mod.FlatLayout()
        self.assertEquals(layout.get_source_candidates('tests/_foo.py'), ['src/foo.py', 'src/foo/__init__.py'])
        self.assertEquals(layout.get_source_candidates('tests/_bar.py'), ['src/bar.py', 'src/bar/__init__.py'])
        self.assertEquals(layout.get_source_candidates('tests/_foo_bar.py'), ['src/foo/bar.py', 'src/foo/bar/__init__.py'])


class TestFollowHierarcyLayout(FileAwareTestCase):
    def setUp(self):
        setUpVimEnvironment()

    def testDetectTestFile(self):
        vimvar['g:PyUnitSourceRoot'] = 'src'
        vimvar['g:PyUnitTestsRoot'] = 'tests'
        layout = mod.FollowHierarchyLayout()
        self.assertTrue(layout.is_test_file('tests/test_foo.py'))
        self.assertTrue(layout.is_test_file('tests/test_foo/test_bar.py'))
        self.assertFalse(layout.is_test_file('foo.py'))
        self.assertFalse(layout.is_test_file('test_foo/test_bar.py'))
        self.assertFalse(layout.is_test_file('tests/foo/test_bar.py'))
        self.assertFalse(layout.is_test_file('src/foo.py'))
        self.assertFalse(layout.is_test_file('src/foo/bar.py'))

    def testDetectTestFileWithAlternatePrefix(self):
        vimvar['g:PyUnitTestPrefix'] = '_'
        vimvar['g:PyUnitSourceRoot'] = 'src'
        vimvar['g:PyUnitTestsRoots'] = 'tests'
        layout = mod.FollowHierarchyLayout()
        self.assertTrue(layout.is_test_file('tests/_foo.py'))
        self.assertTrue(layout.is_test_file('tests/_foo/_bar.py'))
        self.assertFalse(layout.is_test_file('foo.py'))
        self.assertFalse(layout.is_test_file('_foo/_bar.py'))
        self.assertFalse(layout.is_test_file('tests/foo/_bar.py'))
        self.assertFalse(layout.is_test_file('src/foo.py'))
        self.assertFalse(layout.is_test_file('src/foo/bar.py'))

    def testDetectAbsoluteTestFile(self):
        vimvar['g:PyUnitSourceRoot'] = 'src'
        vimvar['g:PyUnitTestsRoots'] = 'tests'
        absdir = os.path.realpath(proj_root)
        layout = mod.FollowHierarchyLayout()
        self.assertTrue(layout.is_test_file('%s/tests/test_foo.py' % absdir))
        self.assertTrue(layout.is_test_file('%s/tests/test_foo/test_bar.py' % absdir))
        self.assertFalse(layout.is_test_file('%s/foo.py' % absdir))
        self.assertFalse(layout.is_test_file('%s/test_foo/test_bar.py' % absdir))
        self.assertFalse(layout.is_test_file('%s/tests/foo/test_bar.py' % absdir))
        self.assertFalse(layout.is_test_file('%s/src/foo.py' % absdir))
        self.assertFalse(layout.is_test_file('%s/src/foo/bar.py' % absdir))

    def testSourceToTestFailsForNonSourceFiles(self):
        vimvar['g:PyUnitSourceRoot'] = 'src'
        layout = mod.FollowHierarchyLayout()
        self.assertRaises(RuntimeError, layout.get_test_file, 'nonsrc/foo.py')
        self.assertRaises(RuntimeError, layout.get_test_file, 'foo.py')
        #self.assertRaises(RuntimeError, layout.get_test_file, 'src.py')

    def testSourceToTest(self):
        vimvar['g:PyUnitSourceRoot'] = 'src'
        layout = mod.FollowHierarchyLayout()
        self.assertEquals(layout.get_test_file('src/foo.py'), 'tests/test_foo.py')
        self.assertEquals(layout.get_test_file('src/bar.py'), 'tests/test_bar.py')
        self.assertEquals(layout.get_test_file('src/bar/baz.py'), 'tests/test_bar/test_baz.py')

    def testSourceToTestWithAlternatePrefix(self):
        vimvar['g:PyUnitSourceRoot'] = 'src'
        vimvar['g:PyUnitTestPrefix'] = '_'
        layout = mod.FollowHierarchyLayout()
        self.assertEquals(layout.get_test_file('src/foo.py'), 'tests/_foo.py')
        self.assertEquals(layout.get_test_file('src/bar.py'), 'tests/_bar.py')
        self.assertEquals(layout.get_test_file('src/bar/baz.py'), 'tests/_bar/_baz.py')

    def testTestToSource(self):
        vimvar['g:PyUnitSourceRoot'] = 'src'
        layout = mod.FollowHierarchyLayout()
        self.assertEquals(layout.get_source_candidates('tests/test_foo.py'), ['src/foo.py', 'src/foo/__init__.py'])
        self.assertEquals(layout.get_source_candidates('tests/test_bar.py'), ['src/bar.py', 'src/bar/__init__.py'])
        self.assertEquals(layout.get_source_candidates('tests/bar/test_baz.py'), ['src/bar/baz.py', 'src/bar/baz/__init__.py'])
        self.assertRaises(RuntimeError, layout.get_source_candidates, 'test_foo.py')

    def testTestToSourceWithAlternatePrefix(self):
        vimvar['g:PyUnitSourceRoot'] = 'src'
        vimvar['g:PyUnitTestPrefix'] = '_'
        layout = mod.FollowHierarchyLayout()
        self.assertEquals(layout.get_source_candidates('tests/_foo.py'), ['src/foo.py', 'src/foo/__init__.py'])
        self.assertEquals(layout.get_source_candidates('tests/_bar.py'), ['src/bar.py', 'src/bar/__init__.py'])
        self.assertEquals(layout.get_source_candidates('tests/bar/_baz.py'), ['src/bar/baz.py', 'src/bar/baz/__init__.py'])
        self.assertRaises(RuntimeError, layout.get_source_candidates, '_foo.py')


class TestPlugin(FileAwareTestCase):
    def setUp(self):
        setUpVimEnvironment()

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
        self.assertTrue(mod.is_test_file('tests/test_foo.py'))

        vimvar['g:PyUnitTestsRoot'] = 'my/test/dir'
        self.assertFalse(mod.is_test_file('tests/test_foo.py'))

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


