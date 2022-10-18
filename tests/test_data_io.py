import os, pytest
import numpy as np
from numpy.testing import assert_array_equal, assert_array_almost_equal
import openmeeg as om
from data_for_testing import simple_test_shapes, find_center_of_triangle
from pyhemo.data_io import *
import tempfile

def test_write_geom_file():
    tmp ='tmp_tri%d' 
    num = np.random.randint(2, 6)
    bnds = simple_test_shapes(num_nested_meshes=num)
    geom, names = {}, []
    for i, bnd in enumerate(bnds):
        geom[tmp % (i+1)] = bnd
        names.append(str(i+1))
    geom_file = './tmp_test.geom'
    write_geom_file(geom, geom_file)
    geometry = om.Geometry(geom_file)
    for filename in [geom_file] + [tmp % (i+1)+'.tri' for i in range(num)]:
        os.remove(filename)
    assert geometry.selfCheck()
    assert len(geometry.domains()) == num+1
    assert geometry.nb_parameters() == np.sum([bnd[0].shape[0]+bnd[1].shape[0]
                                               for bnd in bnds])
    for name in names:
        assert str(geometry.mesh(name)) == name

def test_write_cond_file():
    tmp ='tmp_tri%d' 
    num = np.random.randint(2, 6)
    bnds = simple_test_shapes(num_nested_meshes=num)
    cond, geom = {}, {}
    for i, bnd in enumerate(bnds):
        name = i+1 #num-i
        geom[tmp % (i+1)] = bnd
        cond[tmp % (i+1)] = np.random.rand()
    cond_file, geom_file = './tmp_test.cond', './tmp_test.geom'
    write_geom_file(geom, geom_file)
    write_cond_file(cond, cond_file)
    geometry = om.Geometry(geom_file, cond_file)
    for filename in [geom_file, cond_file] + [tmp % (i+1)+'.tri'
                                              for i in range(num)]:
        os.remove(filename)
    for i, d in enumerate(geometry.domains()):
        if i < len(geometry.domains())-1:
            assert pytest.approx(cond[tmp % (i+1)], 5) == d.conductivity()


def test_write_elec_file():
    tmp ='tmp_tri%d' 
    num = np.random.randint(2, 6)
    bnds = simple_test_shapes(num_nested_meshes=num)
    elec_file = os.path.join(tempfile.mkdtemp(), 'tmp_test.elec')
    elecs = find_center_of_triangle(bnds[-1][0], bnds[-1][1])
    elecs = elecs[::2,:]
    write_elec_file(elecs, elec_file)
    sensors = om.Sensors(elec_file) 
    os.remove(elec_file)
    assert_array_almost_equal(sensors.getPositions().array(), elecs)


def test_write_load_tri():
    num = np.random.randint(3, 50)
    pos, tri = [], []
    pos =  np.random.rand(num*3).reshape((num, 3))
    elems = [i for i in np.arange(num) for j in range(4)]
    while len(elems) % 3 != 0:
        elems.append(np.random.randint(0, num))
    while elems:
        face = []
        for _ in range(3):
            t = np.random.choice(elems)
            face.append(t)
            first_t = [i for i in range(len(elems)) if elems[i] == t][0]
            del elems[first_t]
        tri.append(face)
    tri = np.array(tri)
    tri_file = os.path.join(tempfile.mkdtemp(), 'tmp.tri')
    write_tri(pos, tri, tri_file)
    bnd  = load_tri(tri_file)
    os.remove(tri_file)
    new_pos, new_tri = bnd
    assert_array_equal(pos, new_pos)
    assert_array_equal(tri, new_tri)


def test_write_bnd():
    # not in use anymore?
    assert True

