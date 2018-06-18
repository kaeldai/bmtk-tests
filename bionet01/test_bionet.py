import sys
import os
import h5py
from bmtk.simulator import bionet
#from bmtk.analyzer.spikes_analyzer import spike_files_equal

from bmtk.utils.spike_trains import SpikesFile
from bmtk.utils.cell_vars import CellVarsFile

import matplotlib.pyplot as plt
import numpy as np

#spikes_csv = SpikesFile('expected/spikes.csv')
#print spikes_csv.gids
#for gid in spikes_csv.gids:
#    print spikes_csv.get_spikes(gid)

#spikes_h5 = SpikesFile('expected/spikes.h5')
#print spikes_h5.gids
#for gid in spikes_h5.gids:
#    print spikes_h5.get_spikes(gid)

#print spikes_csv.get_spikes(1)
#print '----'
#print spikes_h5.get_spikes(1)

#print spikes_h5 == spikes_csv

"""
soma_reports = CellVarsFile('output/soma_vars.h5')
print soma_reports.variables
print soma_reports.gids
print soma_reports.t_start, soma_reports.t_stop, soma_reports.dt

data = soma_reports.data(var_name='v', gid=0, time_window=(1000.0, 1100.0))
print len(data)
# exit()


#for gid in soma_reports.gids:
#    print soma_reports.n_compartments(gid)


#plt.plot(soma_reports.time_trace, soma_reports.data(var_name='v', gid=0))
#plt.show()

compartmental_reports = CellVarsFile('output/full_cell_vars.h5')
print compartmental_reports.variables
print compartmental_reports.gids

print compartmental_reports.n_compartments(7)
print compartmental_reports.compartment_ids(gid=7)
#print compartmental_reports.data('v', gid=0, compartments='all').shape
"""

soma_reports = CellVarsFile('output/soma_vars.h5')

data_v_9 = soma_reports.data('v', gid=9, time_window=(2500.0, 3000.0))
data_cai_9 = soma_reports.data('cai', gid=9, time_window=(2500.0, 3000.0))
data_i_mem_9 = soma_reports.data('i_membrane', gid=9, time_window=(2500.0, 3000.0))
print data_i_mem_9




#input_spikes = SpikesFile('output/spikes.h5')
#spikes_df = input_spikes.to_dataframe()

#input_spikes_csv = SpikesFile('output/spikes.csv')
#print input_spikes_csv.to_dataframe()

#print np.array(input_spikes['gids'])


"""
sample_data = h5py.File('sim_output.h5', 'w')

# spikes data
input_spikes = SpikesFile('output/spikes.h5')
spikes_df = input_spikes.to_dataframe()
sample_data.create_dataset('/spikes/gids', data=np.array(spikes_df['gids']))
sample_data.create_dataset('/spikes/timestamps', data=np.array(spikes_df['timestamps']))
sample_data['/spikes/gids'].attrs['sorting'] = 'time'

# soma data
soma_reports = CellVarsFile('output/soma_vars.h5')
soma_grp = sample_data.create_group('/soma')
soma_grp.create_dataset('mapping/time', data=[2500.0, 3000.0, 0.1])
soma_grp.create_dataset('mapping/gids', data=[3])
for var_name in soma_reports.variables:
    soma_grp.create_dataset(var_name, data=soma_reports.data(var_name, gid=3, time_window=(2500.0, 3000.0)))

# compartmental report
ecp_file = h5py.File('output/ecp.h5', 'r')
ecp_grp = sample_data.create_group('/ecp')
ecp_grp.create_dataset('data', data=ecp_file['data'][:, 0])
ecp_grp.create_dataset('channel_id', data=ecp_file['channel_id'])
"""

#compartmental_reports = CellVarsFile('output/full_cell_vars.h5')
#print compartmental_reports.data('v', gid=2, time_window=(2900.0, 3000.0), compartments='all')


#input_spikes = SpikesFile('sim_output.h5')
#print input_spikes.gids

#sample_data.create_dataset('/spike_trains',

#sampled_data

#self._gid_ds = self._h5_handle['/spikes/gids']
#self._timestamps_ds = self._h5_handle['/spikes/timestamps']


def test_network1():
    conf = bionet.Config.from_json('config.json', validate=True)
    conf.build_env()

    graph = bionet.BioNetwork.from_config(conf)
    sim = bionet.BioSimulator.from_config(conf, network=graph)
    sim.run()
    # bionet.nrn.quit_execution()

    #SpikesFile.load(conf['output']['spikes_file'])

    #assert (os.path.exists(conf['output']['spikes_ascii_file']))
    assert (SpikesFile(conf['output']['spikes_file']) == SpikesFile('expected/spikes.csv'))

    soma_reports = CellVarsFile('output/soma_vars.h5')
    print soma_reports.variables
    print soma_reports.gids

    print set(soma_reports.variables) == set(['i_membrane', 'cai', 'vext', 'e_extracellular', 'v'])
    print set(soma_reports.gids) == set([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])



def test_virtual_input():
    import json
    config_base = json.load(open('config_base.json'))
    config_base['inputs'] = {
        "LGN_spikes": {
            "input_type": "spikes",
            "module": "nwb",
            "input_file": "$INPUT_DIR/lgn_spikes.nwb",
            "node_set": "lgn",
            "trial": "trial_0"
        },
        "TW_spikes": {
            "input_type": "spikes",
            "module": "nwb",
            "input_file": "$INPUT_DIR/tw_spikes.nwb",
            "node_set": "tw",
            "trial": "trial_0"
        }
    }

    conf = bionet.Config.from_json('config.json', validate=True)
    conf.build_env()

    graph = bionet.BioNetwork.from_config(conf)
    sim = bionet.BioSimulator.from_config(conf, network=graph)
    sim.run()

    # Check spikes
    assert (SpikesFile(conf['output']['spikes_file']) == SpikesFile('expected/spikes.csv'))

    soma_reports = CellVarsFile('output/soma_vars.h5')
    assert(set(soma_reports.variables) == set(['i_membrane', 'cai', 'vext', 'e_extracellular', 'v']))
    assert(set(soma_reports.gids) == set([0, 1, 2, 3, 4, 5, 6, 7, 8, 9]))



test_virtual_input()

