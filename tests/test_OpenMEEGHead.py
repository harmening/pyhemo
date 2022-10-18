import os, pytest
import numpy as np
import openmeeg as om
from numpy.testing import assert_array_equal, assert_array_almost_equal
from pyhemo.OpenMEEGHead import OpenMEEGHead
import sys
sys.path.append('./tests')
from data_for_testing import simple_test_shapes, find_center_of_triangle
from collections import OrderedDict


def test_OpenMEEGHead():
    # tbd
    tmp ='tmp_tri%d' 
    num = np.random.randint(2, 4)
    bnds = simple_test_shapes(num_nested_meshes=num)
    geom, cond = OrderedDict(), {}
    for i, bnd in enumerate(bnds):
        geom[tmp % (i+1)] = bnd
        cond[tmp % (i+1)] = np.random.rand()
    electrodes = find_center_of_triangle(bnds[-1][0], bnds[-1][1])
    with pytest.raises(ValueError):
        head = OpenMEEGHead(cond, [], electrodes)
    head = OpenMEEGHead(cond, geom, electrodes)
    nb_entries, nb_elements = 0, 0
    for i, bnd in enumerate(bnds):
        pos, tri = bnd
        nb_elements += pos.shape[0] + tri.shape[0] 
        ###nb_entries += len(head.ind['V'][i]) + len(head.ind['p'][i]) ###
        #if i != len(bnds)-1:
        #    nb_entries += len(head.ind['p'][i])
        if i == len(bnds)-1:
            nb_elements -= tri.shape[0]
    #assert nb_elements == nb_entries == head.A.nlin()
    #assert nb_elements == head.A.nlin()
    assert nb_elements == head.A.shape[0]
    ###assert nb_elements == nb_entries
    # if inside out and openmeeg works outside in
    ###assert head.ind['p'][0][-1]+1 == head.A.nlin() 
    assert head.mesh_names[-1] == list(geom.keys())[0] # reversed order
    ###assert head.Ainv != head.A  # the order is important here! ###
    assert (head.h2em >= 0.0).all() and (head.h2em <= 1.0).all()   
    assert int(round(np.sum(head.h2em),0)) == electrodes.shape[0]
    #head.set_cond(cond)
    # random dips
    cortex = bnds[0][0]
    minmax = [(np.min(cortex[:,i]), np.max(cortex[:,i])) for i in range(3)]
    diff = [(minmax[i][1]-minmax[i][0])/3 for i in range(3)]
    minmax = [(minmax[i][0]+diff[i], minmax[i][1]-diff[i]) for i in range(3)]
    diff = [minmax[i][1]-minmax[i][0] for i in range(3)]
    dips = np.random.rand(10,6)
    for i in range(10):
        for j in range(3):
            dips[i][j] = minmax[j][0] + diff[j]*dips[i][j]
    head.add_dipoles(dips)
    assert (dips == head.dipoles).all()
    fn_dips = './test_tmp.dip'
    with open(fn_dips, 'w') as f:
        for d in dips:
            f.write('%f %f %f %f %f %f\n' % (d[0],d[1],d[2], d[3],d[4],d[5]))
    head.add_dipoles(fn_dips)
    #assert assert_array_almost_equal(dips, head.dipoles) 
    os.remove(fn_dips)
    assert head.ind['V'][-1][0] == 0
    with pytest.raises(NotImplementedError):
        head.V('msm')
    V = head.V('dsm')
    assert V.shape == (electrodes.shape[0],10)
    Ainv = head.Ainv
    assert_array_almost_equal(V, head.V('dsm'))


