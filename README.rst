Installation
------------
1. Install the following packages from PyPI:

   - nose_: the unit test runner;
   - nose_machineout_:  The ``machineout`` plugin formats the ``nose`` output
     so that Vim can parse it more easily;
   - vim_bridge_:  This is required for the vim plugin scripts, to call
     directly into Python functions.

2. Clone the git repository::

       git clone git://github.com/nvie/vim-pyunit.git
       cd vim-pyunit

3. Build the plugin.  This simply concatenates two files::
   
       python build.py

4. Copy the generated file ``ftplugin/python_pyunit.vim`` to your
   ``~/.vim/ftplugin`` directory

.. _nose: http://pypi.python.org/pypi/nose
.. _nose_machineout: http://pypi.python.org/pypi/nose_machineout
.. _vim_bridge: http://pypi.python.org/pypi/vim_bridge


Usage
-----
1. Open a Python file (or its corresponding unit test file named
   ``test_<filename>.py``)
2. Press ``<F8>`` to run ``nosetests`` on it

It shows the errors inside a quickfix window, which will allow your to quickly
jump to the error locations by simply pressing ``[Enter]``.


Source files vs. test files
---------------------------
``vim-pyunit`` assumes that you have a single test file for each Python source
file.  The settings ``test_prefix``, ``test_suffix``, ``source_root``,
``tests_root``, and ``tests_structure`` determine how the plugin finds which
test files belong to which source files.


Keyboard mappings
-----------------
By default, the ``vim-pyunit`` plugin defines the following keyboard
mappings:

+----------+------------------------------------------------------------------+
| Keymap   | Description                                                      |
+==========+==================================================================+
| F8       | Run ``nosetests`` for the current file. This mapping can be used |
|          | on both the source file, and on its corresponding test file.     |
+----------+------------------------------------------------------------------+
| Shift+F8 | Run ``nosetests`` for all test files in the project, this is     |
|          | equivalent to running ``nosetests`` in the root of your project. |
+----------+------------------------------------------------------------------+
| F9       | Switch between the source and the corresponding test file. If    |
|          | the source or test file is not yet open, it is opened. The       |
|          | setting ``tests_split_window`` is used to determine where the    |
|          | file needs to be opened screen-wise.                             |
+----------+------------------------------------------------------------------+


Configuration
-------------
The plugin supports setting of the following variables:

+-------------------------------+------------------------------------------------+------------------------------+---------------------------------------+
| Variable                      | Description                                    | Values                       | Default                               |
+===============================+================================================+==============================+=======================================+
| ``show_tests``                | Shows the tests.                               | 0 or 1                       | ``1``                                 |
+-------------------------------+------------------------------------------------+------------------------------+---------------------------------------+
| ``pyunit_cmd``                | The command to run the unit test.              | any string                   | ``"nosetests -q --with-machineout"``  |
+-------------------------------+------------------------------------------------+------------------------------+---------------------------------------+
| ``projroot_indicators``       | List of filenames indicating the               | list of file names           | ``[".git", "setup.py", "setup.cfg"]`` |
|                               | project root.                                  |                              |                                       |
+-------------------------------+------------------------------------------------+------------------------------+---------------------------------------+
| ``projroot_stop_at_home_dir`` | Stop the search for the project root at the    | 0 or 1                       | ``1``                                 |
|                               | user's home dir.                               |                              |                                       |
+-------------------------------+------------------------------------------------+------------------------------+---------------------------------------+
| ``test_prefix``               | The filename prefix to use for test files.     | any string                   | ``"test_"``                           |
+-------------------------------+------------------------------------------------+------------------------------+---------------------------------------+
| ``test_suffix``               | *Not implemented yet*                          | 0 or 1                       | n/a                                   |
+-------------------------------+------------------------------------------------+------------------------------+---------------------------------------+
| ``source_root``               | The relative location where all source files   | directory spec, or empty     | ``""``                                |
|                               | live.                                          |                              |                                       |
+-------------------------------+------------------------------------------------+------------------------------+---------------------------------------+
| ``tests_root``                | The relative location where all tests live.    | directory spec               | ``"tests"``                           |
+-------------------------------+------------------------------------------------+------------------------------+---------------------------------------+
| ``tests_structure``           | Specifies how you wish to organise your tests. | flat, follow-hierarchy       | ``"follow-hierarchy"``                |
+-------------------------------+------------------------------------------------+------------------------------+---------------------------------------+
| ``tests_split_window``        | Specifies where test files should be opened,   | left, right, top, bottom, no | ``"right"``                           |
|                               | when oopened next to the source file. When set |                              |                                       |
|                               | to ``no``, doesn't open a new window at all,   |                              |                                       |
|                               | but reuses the current buffer.                 |                              |                                       |
+-------------------------------+------------------------------------------------+------------------------------+---------------------------------------+


