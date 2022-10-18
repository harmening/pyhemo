import os, numpy as np
from collections import OrderedDict   
from pyhemo.DUNEuroHead import DUNEuroHead
from pyhemo.OpenMEEGHead import OpenMEEGHead

BASEDIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
DATADIR = os.path.join(BASEDIR, 'examples', 'colin')

def load_elecs_dips_txt(fn):
    with open(fn, 'r') as f:
    	elecs = [[float(i) for i in line.split()] for line in f.readlines()]
    return elecs


# common settings
cond = {'air': 2.5*pow(10, -14), 'gray': 0.33, 'white': 0.33, 'csf': 1.78, 'skull':  0.004125, 'scalp': 0.25} 
sensors = load_elecs_dips_txt(os.path.join(DATADIR, 'electrodes_aligned.txt'))
dipoles = load_elecs_dips_txt(os.path.join(DATADIR, 'sourcemodel2000.txt'))
dipoles = np.array(dipoles)[np.random.choice(len(dipoles), 10)]


# BEM
from pyhemo.data_io import load_tri
conductivity = {'scalp': cond['scalp'], 'skull': cond['skull'], 'csf': cond['csf'], 'cortex': cond['white']}
geometry = OrderedDict([('cortex', load_tri(os.path.join(DATADIR, 'cortex.tri'))), 
                        ('csf', load_tri(os.path.join(DATADIR, 'csf.tri'))), 
                        ('skull', load_tri(os.path.join(DATADIR, 'skull.tri'))), 
                        ('scalp', load_tri(os.path.join(DATADIR, 'scalp.tri')))])
bem = OpenMEEGHead(conductivity, geometry, sensors)
print('\nCreated BEM head.\n')

# FEM with 6 tissue types meshed directly from segmentation
mesh_filename = os.path.join(DATADIR, 'mesh6_maxvoxvol5.msh')
fem6 = DUNEuroHead(cond, mesh_filename, sensors)

# FEM of the 4 nested meshes above
mesh_filename = os.path.join(DATADIR, 'bnd4_1922_FEM.mat')
fem4 = DUNEuroHead(conductivity, mesh_filename, sensors)
print('\nCreated FEM heads.\n')

print('Created head instances.\n')

bem.add_dipoles(dipoles)
fem4.add_dipoles(dipoles)
fem6.add_dipoles(dipoles)
print('Added dipoles.\n')


V_bem = {'dsm': bem.V('dsm')}
print('\nCalculated BEM leadfields.\n')

V_fem4 = {}
for sm_type in ['Partial integration', 'Venant', 'Subtraction', 'Spatial Venant']:
    V_fem4[sm_type] = fem4.V(sm_type)
V_fem6 = {}
for sm_type in ['Partial integration', 'Venant', 'Subtraction', 'Spatial Venant']:
    V_fem6[sm_type] = fem6.V(sm_type)
print('\nCalculated FEM leadfields.\n')


print('Calculate Pearson correlation of BEM with different FEMs of (FEM4):')
for sm_type in ['Partial integration', 'Venant', 'Subtraction', 'Spatial Venant']:
    c = np.mean([np.abs(np.corrcoef(V_bem['dsm'][:,i], V_fem4[sm_type][:,i])[0,1]) for i in range(10)])
    print('%s: %f' % (sm_type, c))

print('Calculate Pearson correlation of BEM with different FEMs (FEM6):')
for sm_type in ['Partial integration', 'Venant', 'Subtraction', 'Spatial Venant']:
    c = np.mean([np.abs(np.corrcoef(V_bem['dsm'][:,i], V_fem6[sm_type][:,i])[0,1]) for i in range(10)])
    print('%s: %f' % (sm_type, c))

