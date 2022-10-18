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
            fn_geom = os.path.join(tmp, str(int(random()*100000000))+'.geom')
            write_geom_file(geom_out2inside, fn_geom)
            self.mesh_names = list(geom_out2inside.keys()) # out to inside
        else:
            raise ValueError
        self.geometry = geometry # inside to outside
        self.cond = conductivity
        fn_cond = os.path.join(tmp, str(int(random()*100000000))+'.cond')
        write_cond_file(self.cond, fn_cond)
        self.elec_positions = elec_positions
        fn_elec = os.path.join(tmp, str(int(random()*100000000))+'.elec')
        if isinstance(elec_positions, list) or isinstance(elec_positions,
                                                          np.ndarray):
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
        ##self.ind = self._get_indices_inside_out()
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
        ind['V'] = []#np.zeros((self.geom.nb_meshes(), 2), dtype=int)
        ind['p'] = []#np.zeros((self.geom.nb_meshes(), 2), dtype=int)
        for t in range(len(self.mesh_names), 0, -1):
            tissue = self.mesh_names[t-1]
            mesh = self.geom.mesh(str(t))
            i = ind[tissue]
            V_num = len(mesh.vertices())
            start = 0 if i == len(self.mesh_names)-1 else ind['V'][-1][-1]+1
            ind['V'].append(np.arange(start, start + V_num))

        for t in range(len(self.mesh_names), 0, -1):
            tissue = self.mesh_names[t-1]
            mesh = self.geom.mesh(str(t))
            i = ind[tissue]
            p_num = len(mesh.triangles())
            # the triangles of the outermost mesh are not included in A
            if i == len(self.mesh_names)-1:
                ind['p'].append(np.arange(0))
            elif i == len(self.mesh_names)-2: 
                ind['p'].append(np.arange(ind['V'][-1][-1]+1,
                                          ind['V'][-1][-1]+1 + p_num))  
            else:
                ind['p'].append(np.arange(ind['p'][-1][-1]+1,
                                          ind['p'][-1][-1]+1 + p_num))
        # Daniels version:
        ind['V'] = [lst for lst in reversed(ind['V'])]
        ind['p'] = [lst for lst in reversed(ind['p'])]
        return ind
    
    @property
    def A(self):
        """Compute/return the attribute system matrix A"""
        if not isinstance(self._A, np.ndarray):
            A = om.HeadMat(self.geom) #, self.GAUSS_ORDER)
            self._A = om.Matrix(A).array()
            #self._condition_nb = self.condition_nb
        return self._A
    @property
    def Ainv(self):
        """Compute/return the attribute system matrix A inverse"""
        if not isinstance(self._Ainv, np.ndarray):
            print("Warning: inverting A explicitly...")
            self._Ainv = np.linalg.pinv(self.A)
        return self._Ainv
    @property
    def h2em(self):
        """Compute/return the mapping from outer boundary to electrodes"""
        if not isinstance(self._h2em, np.ndarray):
            h2em = om.Head2EEGMat(self.geom, self.sens)
            self._h2em = om.Matrix(h2em).array()
        return self._h2em

    def add_dipoles(self, dipole_locations):
        if isinstance(dipole_locations, list) or isinstance(dipole_locations,
                                                            np.ndarray):
            self.dipoles = dipole_locations 
            fn_dip = os.path.join(tempfile.mkdtemp(),
                                  'dipoles_'+str(int(random()*100000000)))
            write_dip_file(self.dipoles, fn_dip)
        elif isinstance(dipole_locations, str):
            fn_dip = dipole_locations
            with open(fn_dip, 'r') as f:
                lines = f.readlines()
            self.dipoles = [[float(x) for x in line.split()] for line in lines]
        #self.dipoles = np.array(self.dipoles)
        #self.dipoles = om.Matrix(np.asfortranarray(self.dipoles))
        self.dipole_file = fn_dip 
        self._V = None

    def V(self, source_model_type):
        if not isinstance(self._V, dict):
            self._V = {}
        if not source_model_type in self._V.keys():
            if source_model_type == 'dsm':
                domain = self.mesh_names[0]
            else:
                raise NotImplementedError
            #dipoles = om.Matrix(self.dipoles)
            dipoles = om.Matrix(np.asfortranarray(self.dipoles))
            dsm = om.DipSourceMat(self.geom, dipoles, domain)
            dsm = om.Matrix(dsm).array()
            if isinstance(self._Ainv, np.ndarray):
                # use precomputed Ainv
                L = self.h2em.dot(np.dot(self.Ainv, dsm))
            else:
                # faster
                C = np.linalg.solve(self.A, dsm)
                L = np.dot(self.h2em, C)
            self._V[source_model_type] = L
        return self._V[source_model_type]
