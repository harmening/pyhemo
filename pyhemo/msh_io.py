import sys, os, re
import numpy as np
import h5py, scipy.io as sio


def elecs_mat2txt(fn):
    data = {}
    with h5py.File(fn, 'r') as f:
        for k, v in f.items():
            data[k] = v
        if 'elec_aligned' in data.keys():
            elecs = np.array(data['elec_aligned']['chanpos'])
        else:
            elecs = np.array(data['elec']['chanpos'])
    if elecs.shape[0] == 3 and elecs.shape[1] != 3:
        elecs = elecs.T
    with open(fn[:-4]+'.txt', 'w') as f:
        for elec in elecs:
            f.write('%f %f %f\n' % (elec[0], elec[1], elec[2]))
    return fn[:-4]+'.txt'

def sources_mat2txt(fn):
    data = {}
    try:
        with h5py.File(fn, 'r') as f:
            for k, v in f.items():
                data[k] = v
            sources = np.array(data['sourcemodel']['pos'])
            if 'vec' in data['sourcemodel'].keys():
                vec = np.array(data['sourcemodel']['vec'])
    except:
        data = sio.loadmat(fn)
        sources = data['sourcemodel'][0][0][0]
        vec = data['sourcemodel'][0][0][1]
    if sources.shape[0] == 3 and sources.shape[1] != 3:
        sources = sources.T
        vec = vec.T
    with open(fn[:-4]+'.txt', 'w') as f:
        for source, v in zip(sources, vec):
            #f.write('%f %f %f\n' % (source[0], source[1], source[2]))
            f.write('%f %f %f %f %f %f\n' % (source[0], source[1], source[2], v[0], v[1], v[2]))
    return fn[:-4]+'.txt'


def load_msh(filename):
    nodes = {}
    elements = {}
    labels = {}
    names = {}
    num_nodes, num_elems, num_names = None, None, None
    two_lines = []
    with open(filename, 'r') as f:
        current = None
        for line in f.readlines():
            if line.strip().startswith('$End'):
                current = None
            elif line.strip().startswith('$MeshFormat'):
                current = 'format'
            elif line.strip().startswith('$Nodes'):
                current = 'nodes'
            elif line.strip().startswith('$Elements'):
                current = 'elements'
            elif line.strip().startswith('$PhysicalNames'):
                current = 'names'
            elif current == 'format':
                print('Format version: %s' % line.strip())
            elif current == 'nodes':
                if not num_nodes:
                    num_nodes = int(line.strip())
                else:
                    node = [l.strip() for l in line.split()]
                    node_idx = int(node[0])
                    nodes[node_idx] = [float(node[1]), float(node[2]), float(node[3])]
            elif current == 'elements':
                if not num_elems:
                    num_elems = int(line.strip())
                elif not two_lines:
                    elem = [e.strip() for e in line.split()]
                    elem_idx = int(elem[0])
                    elem_type = int(elem[1])
                    num_of_tags = int(elem[2])
                    phys_entity = int(elem[3])
                    elem_geom_entity = int(elem[4])
                    if num_of_tags == 2: # from msh_io
                        elements[elem_idx] = [int(elem[3+num_of_tags+ii]) for ii in range(4)]
                        labels[elem_idx] = elem_geom_entity
                    elif num_of_tags == 3: # from iso2mesh
                        two_lines = [elem_idx, elem_geom_entity]
                    else:
                        raise NotImplementedError
                else: # second part of element info
                    elem_idx, elem_geom_entity = two_lines
                    elem = [e.strip() for e in line.split()]
                    elements[elem_idx] = [int(elem[ii]) for ii in range(4)]
                    labels[elem_idx] = elem_geom_entity
                    two_lines = []
            elif current == 'names':
                if not num_names:
                    num_names = int(line.strip())
                else:
                    region_dim = int(line.split()[0].strip())
                    names_idx = int(line.split()[1].strip())
                    names[names_idx] = line.split()[2].strip().replace('"', '')
            else:
                raise ValueError

    assert num_nodes == len(nodes)
    assert num_elems == len(elements)
    assert num_names == len(names)
   
    nodes = [n for _, n in sorted(nodes.items())]
    elements = [e for _, e in sorted(elements.items())]
    labels = [l for _, l in sorted(labels.items())]
    return nodes, elements, labels, names


def write_msh(pos, tet, tissue, targetfilename):
    with open(targetfilename, 'w') as f:
        f.write('$MeshFormat\n2.2 0 8\n$EndMeshFormat\n')
        # Nodes 
        f.write('$Nodes\n%d\n' % len(pos))
        for i, node in enumerate(pos):
            f.write('%d %s %s %s\n' % (i+1, node[0], node[1], node[2]))
        f.write('$EndNodes\n')
        # Elements 
        assert np.min(tet) == 1
        f.write('$Elements\n%d\n' % len(tet))
        elem_type, num_of_tags, phys_entity = 4, 2, 0
        t_idx = 1
        for t in tet:
            f.write('%d %d %d %d %d %d %d %d %d\n' % (t_idx, elem_type, num_of_tags,
                phys_entity, t[4], t[0], t[1], t[2], t[3]))
            t_idx += 1
        assert t_idx == len(tet)+1
        f.write('$EndElements\n')
        # Physical Names
        assert len(tissue) == np.max(np.array(tet)[:,4])
        f.write('$PhysicalNames\n%d\n' % len(tissue))
        region_dim = 3
        for t, tiss in enumerate(tissue):
            f.write('%d %d "%s"\n' % (region_dim, t+1, tiss))
        f.write('$EndPhysicalNames')


def mat2msh(matfile):
    data = sio.loadmat(matfile)
    data = data['mesh'][0][0]
    if matfile.split('/')[-1].startswith('NY'):
        pos = data[0]  
        label = data[1][0]
        tet = data[2]  
        try:
            tissue = [data[3][0][t][0] for t in range(len(data[3]))]
        except:
            tissue = [data[3][t][0] for t in range(len(data[3]))]
        unit = data[4][0]
    else: # from own segmentation
        pos = data[0]
        tet = data[1]
        tri = data[2]
        tissue = [data[3][t][0] for t in range(len(data[3]))]
        tet = np.concatenate((tet, np.array(tissue)[:,np.newaxis]), axis=1)
        tissue = [data[5][0][t][0] for t in range(len(data[5][0]))]
        unit = data[4][0]
    #assert unit == 'mm'
    write_msh(pos[:,:3], tet, tissue, matfile[:-4]+'.msh')
    return matfile[:-4]+'.msh'
"""
def mat2msh(matfile):
    data = sio.loadmat(matfile)
    data = data['mesh'][0][0]
    pos = data[0]
    tet = data[1]
    tri = data[2]
    tissue = [data[3][0][t][0] for t in range(len(data[3][0]))]
    unit = data[4][0]
    #assert unit == 'mm'
    write_msh(pos[:,:3], tet, tissue, matfile[:-4]+'.msh')
    return matfile[:-4]+'.msh'
"""


if __name__ == '__main__':
    """
    Run for example as
    python msh_io.py mesh5.mat
    """
    filenames = [arg for arg in sys.argv[1:]]
    for i, matfile in enumerate(filenames):
        if matfile.endswith('.mat'):
            _ = mat2msh(matfile)
        else:
            raise NotImplementedError

        #nodes, elements, labels, names = load_msh(matfile[:-4]+'.msh')
