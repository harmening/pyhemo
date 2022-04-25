import os, pytest
import numpy as np
import duneuropy as dp
from pyhemo.DUNEuroHead import DUNEuroHead
import sys
sys.path.append('./tests')
from data_for_testing import load_elecs_dips_txt

BASEDIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__))) 
DATADIR = os.path.join(BASEDIR, 'tests', 'test_data')

def test_DUNEuroHead():
    # -> simple test shape: 2 nested icos
    mesh_filename = os.path.join(DATADIR, 'icospheres.mat')    
    elec_filename = os.path.join(DATADIR, 'electrodes_ico162.txt')    
    cond = {'icosphere162': 1.79, 'icosphere42': 0.33}
    sensors = load_elecs_dips_txt(elec_filename) 
    # different constructors
    fem1 = DUNEuroHead(cond, mesh_filename, sensors)
    fem2 = DUNEuroHead(cond, mesh_filename[:-4]+'.msh', sensors)
    # electrodes
    assert len(fem1.electrodes) == len(sensors) 
    e = np.random.choice(len(sensors), 1)[0]
    assert (fem1.electrodes[e] == sensors[e])
    # h2em
    assert fem1.h2em.shape == (len(fem1.electrodes), len(fem1.nodes))
    # dipoles
    is_inner_elem = [l == 1 for k, l in sorted(fem1.labels.items())]
    inner_elems = fem1.elems[is_inner_elem]
    inner_node_idx = list(set(inner_elems.flatten()))
    dipoles = [fem1.nodes[inner_node_idx[dip_idx]] for dip_idx in np.random.choice(len(inner_node_idx), 2)]
    fem1.add_dipoles(dipoles)
    assert np.array(fem1.dipoles).shape == (2,3)
    # V
    sm_type = np.random.choice(['Partial integration', 'Venant', 'Subtraction', 'Spatial Venant'])
    V = fem1.V(sm_type)
    assert V.shape == (len(sensors), 2*3)

