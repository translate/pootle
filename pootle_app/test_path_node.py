import shutil
import os

import py.test

from django.conf import settings

from pootle_app.path_node import *

def make_file(filename):
    f = open(filename, 'w+')
    f.write('Fake file')
    f.close()

def make_files(root, tree):
    for key, val in tree.iteritems():
        child_path = os.path.join(root, key)
        if isinstance(val, dict):
            os.makedirs(child_path)
            make_files(child_path, val)
        else:
            make_file(child_path)

def find_child(path_node, child_name):
    return [child for child in path_node if child.short_name == child_name][0]

def test_gnu_path_node_simple():
    tree = {
        'test_dir': {
            'file_0.po': '',
            'file_1.po': '',
            'file_2.po': '',
            }
        }

    root_dir = os.path.join(settings.PODIRECTORY, 'test_dir')
    shutil.rmtree(root_dir, ignore_errors=True)
    make_files(settings.PODIRECTORY, tree)

    p = GNUPathNode(root_dir, PathShared('po', None))
    children = list(p)
    assert set(str(child) for child in children) == set(['file_0', 'file_1', 'file_2'])
    assert not p._is_pseudo_dir()
    assert p.is_dir
    assert not p.is_translation_file

    root = p.parent
    assert root.is_root
    assert py.test.raises(Exception, lambda: root.parent)
    assert root._full_path == settings.PODIRECTORY

    child_0 = find_child(p, 'file_0')
    assert child_0.parent == p
    assert child_0._is_pseudo_dir()
    assert child_0.is_dir
    assert not child_0.is_translation_file
    assert py.test.raises(Exception, lambda: child_0.real_path)

    grand_children = list(child_0)
    assert list(str(grand_child) for grand_child in grand_children) == ['file_0.po']
    grand_child = grand_children[0]
    assert grand_child.parent == child_0
    assert grand_child.parent.parent == p
    assert not grand_child._is_pseudo_dir()
    assert not grand_child.is_dir
    assert grand_child.is_translation_file
    assert grand_child.real_path == os.path.join(root_dir, 'file_0.po')
    assert os.path.exists(grand_child.real_path)

