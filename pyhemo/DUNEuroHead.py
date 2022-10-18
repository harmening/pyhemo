#!/usr/bin/env python
import duneuropy as dp
import numpy as np
import os
from pyhemo.msh_io import mat2msh, load_msh, elecs_mat2txt, sources_mat2txt

class DUNEuroHead(object):
    def __init__(self, conductivity, geometry, elec_positions):
        # Geometry
        if isinstance(geometry, str):
            if geometry.endswith('.mat') and not os.path.exists(geometry[:-4]+'.msh'):
                geometry = mat2msh(geometry)
            no, el, lab, tiss = load_msh(geometry[:-4]+'.msh')
        elif isinstance(geometry, list):
            no, el, lab, tiss = geometry
        else:
            raise ValueError
        lab = {idx+1: l for idx, l in enumerate(lab)}
        el = np.array(el)
        el -= np.min(el)
        self.nodes = no
        self.elems = el
        self.labels = lab
        self.names = tiss
        # Conductivity
        if isinstance(conductivity, dict):
            tensors = []
            for idx, tissue in sorted(self.names.items()):
                tensors += [conductivity[tissue] * np.identity(3)]
            voxellabels = [l-1 for idx, l in sorted(lab.items())]
        else:
            raise ValueError
        # Driver
        config = {
            'type' : 'fitted',
            'solver_type' : 'cg',
            'element_type' : 'tetrahedron',
            'volume_conductor' : {
                'grid' : {
                    'elements': self.elems,
                    'nodes': self.nodes
                },
                'tensors' : {
                     'labels' : voxellabels,
                     'tensors' : tensors
                }
            },
            'solver' : {'verbose' : 1}
        }
        self.driver = dp.MEEGDriver3d(config)
        # Electrodes
        if isinstance(elec_positions, list) or isinstance(elec_positions, np.ndarray):
            self.electrodes = elec_positions
        elif isinstance(elec_positions, str):
            if elec_positions.endswith('.mat'):
                elec_positions = elecs_mat2txt(elec_positions)
            if not elec_positions.endswith('.txt'):
                raise ValueError
            with open(elec_positions, 'r') as f:
                lines = f.readlines()
            self.electrodes = lines
            self.electrodes = [[float(x) for x in line.split()] for line in self.electrodes]
        else:
            raise ValueError
        electrodes = [dp.FieldVector3D(elec) for elec in self.electrodes]
        electrode_config = {
            'type' : 'closest_subentity_center',
            'codims' : [3]
        }
        self.driver.setElectrodes(electrodes, electrode_config)
        
        self._h2em = None # tm
        self._V = None
    
    @property
    def h2em(self):
        """Compute/return the attribute transfer matrix h2em"""
        if not isinstance(self._h2em, np.ndarray):
            self._h2em = np.array(self.driver.computeEEGTransferMatrix({
                'solver.reduction' : 1e-12,
                'numberOfThreads' : 2
            })[0])
        return self._h2em
    
    def add_dipoles(self, dipole_locations):
        if isinstance(dipole_locations, list) or isinstance(dipole_locations, np.ndarray):
            self.dipoles = dipole_locations 
        elif isinstance(dipole_locations, str):
            if dipole_locations.endswith('.mat'):
                dipole_locations = sources_mat2txt(dipole_locations)
            with open(dipole_locations, 'r') as f:
                lines = f.readlines()
            self.dipoles = [[float(x) for x in line.split()] for line in lines]
        self._V = None
    
    #@property
    def V(self, source_model_type):
        if not isinstance(self._V, dict):
            self._V = {}
        if not source_model_type in self._V.keys():
            if len(self.dipoles[0]) > 3:
                pos = [[x for x in line[:3]] for line in self.dipoles]
                mom = [[x for x in line[3:]] for line in self.dipoles]
                dipoles = [dp.Dipole3d(p,m) for p,m in zip(pos, mom)]
            elif len(self.dipoles[0]) == 3:
                dipoles = []
                for p in self.dipoles:
                    dipoles.append(dp.Dipole3d(p, [1, 0, 0]))
                    dipoles.append(dp.Dipole3d(p, [0, 1, 0]))
                    dipoles.append(dp.Dipole3d(p, [0, 0, 1]))
            else:
                raise ValueError
            if source_model_type == 'Partial integration':
                source_model_config = {'type' : 'partial_integration'}
            elif source_model_type == 'Venant':
                source_model_config = {
                    'type' : 'venant',
                    'numberOfMoments' : 3,
                    'referenceLength' : 20,
                    'weightingExponent' : 1,
                    'relaxationFactor' : 1e-6,
                    'mixedMoments' : False,
                    'restrict' : False,
                    'initialization' : 'closest_vertex'
                }
            elif source_model_type == 'Subtraction':
                source_model_config = {
                    'type' : 'subtraction',
                    'intorderadd' : 2,
                    'intorderadd_lb' : 2
                }
            elif source_model_type == 'Spatial Venant':
                source_model_config = {
                    'type' : 'spatial_venant',
                    'numberOfMoments' : 3,
                    'referenceLength' : 20,
                    'weightingExponent' : 1,
                    'relaxationFactor' : 1e-6,
                    'mixedMoments' : True,
                    'restrict' : True,
                    'initialization' : 'single_element',
                    'extensions' : ['vertex'],
                    'intorderadd' : 2
                }
            else:
                raise NotImplementedError
            V = self.driver.applyEEGTransfer(self.h2em, dipoles, {
                'source_model' : source_model_config,
                'post_process' : True,
                'subtract_mean' : True,
                'numberOfThreads' : 2
            })[0]
            self._V[source_model_type] = np.array(V).T # elecs x sources
            #if len(self.dipoles[0]) == 3:
            #    self._V = self._V.reshape((len(self.electrodes), len(self.dipoles[0]), 3))
        return self._V[source_model_type]
