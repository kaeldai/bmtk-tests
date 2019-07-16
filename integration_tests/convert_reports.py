import os
import h5py
import numpy as np

from bmtk.utils.sonata.utils import add_hdf5_magic, add_hdf5_version


path = 'bio_450cells_exact/expected'
report_name = 'ecp'
pop_name = 'cortex'
units = 'mV'
variable = 'V_m'

reports_h5 = h5py.File(os.path.join(path, '{}.h5'.format(report_name)), 'r')

with h5py.File(os.path.join(path, '{}.new.h5'.format(report_name)), 'w') as h5:
    add_hdf5_magic(h5)
    add_hdf5_version(h5)

    h5_root = h5.create_group('/ecp')
    reports_h5.copy('/data', h5_root)
    h5_root['data'].attrs['units'] = 'mV'
    # h5_root['data'].attrs['variable'] = variable
    reports_h5.copy('/channel_id', h5_root)
    #h5_root['mapping/element_ids'] = h5_root['mapping/element_id']
    #del h5_root['mapping/element_id']
    #h5_root['mapping/node_ids'] = h5_root['mapping/gids']
    #del h5_root['mapping/gids']
    #h5_root['mapping/time'].attrs['units'] = 'ms'
    h5_root.create_dataset('/ecp/time', data=np.array([0.0, 1000.0, 0.1], dtype=np.float))
    h5_root['/ecp/time'].attrs['units'] = 'ms'


'''
path = 'point_120cells/expected'
report_name = 'membrane_potential'
pop_name = 'cortex'
units = 'mV'
variable = 'V_m'

reports_h5 = h5py.File(os.path.join(path, '{}.h5'.format(report_name)), 'r')

with h5py.File(os.path.join(path, '{}.new.h5'.format(report_name)), 'w') as h5:
    add_hdf5_magic(h5)
    add_hdf5_version(h5)

    h5_root = h5.create_group('/report/{}'.format(pop_name))
    reports_h5.copy('/data', h5_root)
    h5_root['data'].attrs['units'] = units
    h5_root['data'].attrs['variable'] = variable
    reports_h5.copy('/mapping', h5_root)
    h5_root['mapping/element_ids'] = h5_root['mapping/element_id']
    del h5_root['mapping/element_id']

    h5_root['mapping/node_ids'] = h5_root['mapping/gids']
    del h5_root['mapping/gids']

    h5_root['mapping/time'].attrs['units'] = 'ms'
'''


'''
path = 'bio_450cells_exact/expected'
report_name = 'calcium_concentration'
pop_name = 'internal'
units = 'mM'
variable = 'cai'

reports_h5 = h5py.File(os.path.join(path, 'cell_vars.h5'.format(report_name)), 'r')

with h5py.File(os.path.join(path, 'calcium_concentration.h5'.format(report_name)), 'w') as h5:
    add_hdf5_magic(h5)
    add_hdf5_version(h5)

    h5_root = h5.create_group('/report/{}'.format(pop_name))
    reports_h5.copy('/cai/data', h5_root)
    h5_root['data'].attrs['units'] = 'mM'
    h5_root['data'].attrs['variable'] = 'cai'
    reports_h5.copy('/mapping', h5_root)
    h5_root['mapping/element_ids'] = h5_root['mapping/element_id']
    del h5_root['mapping/element_id']

    h5_root['mapping/node_ids'] = h5_root['mapping/gids']
    del h5_root['mapping/gids']

    h5_root['mapping/time'].attrs['units'] = 'ms'

with h5py.File(os.path.join(path, 'membrane_potential.h5'.format(report_name)), 'w') as h5:
    add_hdf5_magic(h5)
    add_hdf5_version(h5)

    h5_root = h5.create_group('/report/{}'.format(pop_name))
    reports_h5.copy('/v/data', h5_root)
    h5_root['data'].attrs['units'] = 'mV'
    h5_root['data'].attrs['variable'] = 'V'
    reports_h5.copy('/mapping', h5_root)
    h5_root['mapping/element_ids'] = h5_root['mapping/element_id']
    del h5_root['mapping/element_id']

    h5_root['mapping/node_ids'] = h5_root['mapping/gids']
    del h5_root['mapping/gids']

    h5_root['mapping/time'].attrs['units'] = 'ms'
'''
