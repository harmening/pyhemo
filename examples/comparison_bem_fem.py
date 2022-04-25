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


# FEM 
mesh_filename = os.path.join(DATADIR, 'mesh6_maxvoxvol2.msh')
fem = DUNEuroHead(cond, mesh_filename, sensors)
print('\nCreated FEM head.\n')

print('Created head instances.\n')

bem.add_dipoles(dipoles)
fem.add_dipoles(dipoles)
print('Added dipoles.\n')


V_bem = {'dsm': bem.V('dsm')}
print('\nCalculated BEM leadfields.\n')

V_fem = {}
for sm_type in ['Partial integration', 'Venant', 'Subtraction', 'Spatial Venant']:
    V_fem[sm_type] = fem.V(sm_type)
print('\nCalculated FEM leadfields.\n')


print('Calculate Pearson correlation of BEM with different FEMs:')
for sm_type in ['Partial integration', 'Venant', 'Subtraction', 'Spatial Venant']:
    c = np.mean([np.abs(np.corrcoef(V_bem['dsm'][:,i], V_fem[sm_type][:,i])[0,1]) for i in range(10)])
    print('%s: %f' % (sm_type, c))


