import os, pytest
import numpy as np
#from numpy.testing import assert_array_equal, assert_array_almost_equal
import duneuropy as dp 
from data_for_testing import load_elecs_dips_txt
from pyhemo.msh_io import *

BASEDIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__))) 
DATADIR = os.path.join(BASEDIR, 'tests', 'test_data')


def test_elecs_mat2txt():
    # still in use?
    assert True

def test_sources_mat2txt():
    # still in use?
    assert True

def test_load_msh():
    mesh_filename = os.path.join(DATADIR, 'icospheres.msh')
    no, el, lab, tiss = load_msh(mesh_filename)
    with open(mesh_filename, 'r') as f:
        lines = [l for l in f.readlines()]
    if lines[3].startswith('$Nodes'):
        num_nodes = np.int(lines[4].strip())
        assert np.array(no).shape == (num_nodes, 3)
    if lines[-1].startswith('$EndPhysicalNames'):
        last_tiss = lines[-2].split()[-1].strip('"')
        assert last_tiss in tiss.values()
    return

def test_write_msh():
    nodes = np.random.rand(5,3)
    elems = [[1, 2, 3, 4, 1], [2, 3, 4, 5, 2]]
    targetfn = 'tmp_test.msh'
    write_msh(nodes, elems, ['tet0', 'tet1'], targetfn)
    with open(targetfn, 'r') as f:
        lines = [l for l in f.readlines()]   
    os.remove(targetfn)
    assert lines[3].startswith('$Nodes')
    assert np.int(lines[4].strip()) == 5
    assert lines[11].startswith('$Elements')
    assert np.int(lines[13].split()[0]) == 1
    assert np.int(lines[14].split()[0]) == 2
    

def test_mat2msh():
    # still in use?
    assert True


