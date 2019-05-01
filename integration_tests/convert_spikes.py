import os
import h5py
import numpy as np

from bmtk.utils.sonata.utils import add_hdf5_magic, add_hdf5_version


path = 'point_450glifs/expected'
pop_name = 'internal'

spikes_h5 = h5py.File(os.path.join(path, 'spikes.h5'), 'r')
sorting = 'by_{}'.format(spikes_h5['/spikes'].attrs['sorting'])
timestamps = spikes_h5['/spikes/timestamps'][()]
node_ids = spikes_h5['/spikes/gids'][()]

with h5py.File(os.path.join(path, 'spikes.new.h5'), 'w') as h5:
    add_hdf5_magic(h5)
    add_hdf5_version(h5)

    pop_grp = h5.create_group('/spikes/{}'.format(pop_name))
    pop_grp.attrs['sorting'] = 'by_time'
    pop_grp.create_dataset('node_ids', data=node_ids, dtype=np.uint32)
    pop_grp.create_dataset('timestamps', data=timestamps, dtype=np.float)
    pop_grp['timestamps'].attrs['units'] = 'ms'
