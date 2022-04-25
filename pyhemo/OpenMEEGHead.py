#!/usr/bin/env python
from __future__ import print_function
import os, itertools, tempfile
from random import random 
from shutil import copyfile
import numpy as np, openmeeg as om
from pyhemo.data_io import *
from pyhemo.geometry import create_geometry
from collections import OrderedDict


class OpenMEEGHead(object):
    def __init__(self, conductivity, geometry, elec_positions):      
        tmp = tempfile.mkdtemp()
        if isinstance(geometry, dict):
            geom_out2inside = OrderedDict([(tissue, bnd) for tissue, bnd in
                                           reversed(geometry.items())])
            fn_geom = os.path.join(tmp, 'geom_'+str(random()))
            write_geom_file(geom_out2inside, fn_geom)
            self.mesh_names = list(geom_out2inside.keys()) # out to inside
        else:
            raise ValueError
        self.geometry = geometry # inside to outside
        self.cond = conductivity
        fn_cond = os.path.join(tmp, 'cond_'+str(random()))
        write_cond_file(self.cond, fn_cond)
        self.elec_positions = elec_positions
        fn_elec = os.path.join(tmp, 'elec_'+str(random()))
        if isinstance(elec_positions, list) or isinstance(elec_positions, np.ndarray):
            write_elec_file(elec_positions, fn_elec)
        elif isinstance(elec_positions, str):
            copyfile(elec_positions, fn_elec)
        else:
            raise ValueError
        self.geom, self.sens = create_geometry(fn_geom, fn_cond, fn_elec)     
        for fn in [fn_geom, fn_cond, fn_elec]:
            os.remove(fn)    
        if isinstance(geometry, dict):
            for tissue in geometry.keys(): 
                os.remove(os.path.join(tmp, tissue+'.tri'))
        self.GAUSS_ORDER = 3
        #self.ind = self._get_indices_inside_out()
        self.ind = self._get_indices_outside_in()
        self._A = None
        self._Ainv = None
        self._h2em = None
        self._V = None
        self._condition_nb = None

    def _get_indices_outside_in(self):
        #idx = [i for i in range(self.geom.nb_meshes())]
        ind = {tissue: i for i, tissue in enumerate(self.mesh_names)}
        # From outside to inside
        ind['V'] = []#np.zeros((self.geom.nb_meshes(), 2), dtype=np.int)
        ind['p'] = []#np.zeros((self.geom.nb_meshes(), 2), dtype=np.int)
        for tissue, mesh in zip(reversed(self.mesh_names), self.geom.meshes()):
            i = ind[tissue]
            V_num = mesh.nb_vertices()
            start = 0 if i == len(self.mesh_names)-1 else ind['V'][-1][-1]+1
            ind['V'].append(np.arange(start, start + V_num))

        for tissue, mesh in zip(reversed(self.mesh_names), self.geom.meshes()):
            i = ind[tissue]
            p_num = mesh.nb_triangles()
            if i == len(self.mesh_names)-1: # the triangles of the outermost mesh are not included in A
                ind['p'].append(np.arange(0))
            elif i == len(self.mesh_names)-2: 
                ind['p'].append(np.arange(ind['V'][-1][-1]+1, ind['V'][-1][-1]+1 + p_num))  
            else:
                ind['p'].append(np.arange(ind['p'][-1][-1]+1, ind['p'][-1][-1]+1 + p_num))
        # Daniels version:
        ind['V'] = [lst for lst in reversed(ind['V'])]
        ind['p'] = [lst for lst in reversed(ind['p'])]
        return ind
    
    @property
    def A(self):
        """Compute/return the attribute system matrix A"""
        if not self._A:
            self._A = om.HeadMat(self.geom, self.GAUSS_ORDER)
            #self._condition_nb = self.condition_nb
        return self._A
    @property
    def Ainv(self):
        """Compute/return the attribute system matrix A inverse"""
        if not self._Ainv:
            # deepcopy
            fn_A = os.path.join(tempfile.mkdtemp(), 'A_'+str(random()))
            self.A.save(fn_A)
            self._Ainv = self._A
            self._Ainv.invert()
            self._A = om.SymMatrix(fn_A)
            os.remove(fn_A)
        return self._Ainv
    @property
    def h2em(self):
        """Compute/return the mapping from outer boundary to electrodes"""
        if not self._h2em:
            self._h2em = om.Head2EEGMat(self.geom, self.sens)
        return self._h2em

    def asnp(self, openmeeg_matrix):
        """Convert openmeeg_matrix to numpy array"""
        return om2np(openmeeg_matrix)

    def add_dipoles(self, dipole_locations):
        if isinstance(dipole_locations, list) or isinstance(dipole_locations, np.ndarray):
            self.dipoles = dipole_locations 
            fn_dip = os.path.join(tempfile.mkdtemp(), 'dipoles_'+str(random()))
            write_dip_file(self.dipoles, fn_dip)
        elif isinstance(dipole_locations, str):
            with open(dipole_locations, 'r') as f:
                lines = f.readlines()
            self.dipoles = [[float(x) for x in line.split()] for line in lines]
        self.dipole_file = fn_dip 

    def V(self, source_model_type):
        if not self._V:
            if source_model_type == 'dsm':
                domain = self.mesh_names[0]
            #elif source_model_type == 'eit':
            #    domain = self.mesh_names[-1]
            else:
                raise NotImplementedError
            dipoles = om.Matrix(self.dipole_file) 
            GAUSS_ORDER = 3
            use_adaptive_integration = True
            dsm = om.DipSourceMat(self.geom, dipoles, GAUSS_ORDER, use_adaptive_integration, domain)
            #K = self.Ainv * dsm
            #L = self.h2em * K
            L = self.h2em * self.Ainv * dsm
            self._V = om2np(L).astype(np.float32)
        return self._V
    

def om2np(om_matrix_tmp):
    np_matrix = np.zeros((om_matrix_tmp.nlin(), om_matrix_tmp.ncol()))
    for i in range(om_matrix_tmp.nlin()):
        for j in range(om_matrix_tmp.ncol()):
            np_matrix[i,j] = om_matrix_tmp(i,j)
    return np_matrix
