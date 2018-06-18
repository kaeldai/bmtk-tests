import os
import h5py
import numpy as np
import json
import tempfile
import shutil

from bmtk.simulator import bionet
from bmtk.utils.spike_trains import SpikesFile
from bmtk.utils.cell_vars import CellVarsFile


def save_data(sim_type, output_dir):
    save_file = 'expected/sim_output_{}.h5'.format(sim_type)

    sample_data = h5py.File(save_file, 'w')

    # spikes data
    input_spikes = SpikesFile(os.path.join(output_dir, 'spikes.h5'))
    spikes_df = input_spikes.to_dataframe()
    sample_data.create_dataset('/spikes/gids', data=np.array(spikes_df['gids']))
    sample_data.create_dataset('/spikes/timestamps', data=np.array(spikes_df['timestamps']))
    sample_data['/spikes/gids'].attrs['sorting'] = 'time'

    # soma data
    soma_reports = CellVarsFile(os.path.join(output_dir, 'soma_vars.h5'))
    soma_grp = sample_data.create_group('/soma')
    soma_grp.create_dataset('mapping/time', data=[2500.0, 3000.0, 0.1])
    soma_grp.create_dataset('mapping/gids', data=[3])
    for var_name in soma_reports.variables:
        soma_grp.create_dataset(var_name, data=soma_reports.data(var_name, gid=3, time_window=(2500.0, 3000.0)))

    # compartmental report
    ecp_file = h5py.File(os.path.join(output_dir, 'ecp.h5'), 'r')
    ecp_grp = sample_data.create_group('/ecp')
    ecp_grp.create_dataset('data', data=ecp_file['data'][:, 0])
    ecp_grp.create_dataset('channel_id', data=ecp_file['channel_id'])


def sim_virt():
    output_dir = tempfile.mkdtemp()
    config_base = json.load(open('config_base.json'))
    config_base['manifest']['$OUTPUT_DIR'] = output_dir
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

    conf = bionet.Config.from_dict(config_base, validate=True)
    conf.build_env()

    graph = bionet.BioNetwork.from_config(conf)
    sim = bionet.BioSimulator.from_config(conf, network=graph)
    sim.run()

    save_data('virt', output_dir)
    shutil.rmtree(output_dir)


def sim_iclamp():
    output_dir = tempfile.mkdtemp()
    config_base = json.load(open('config_base.json'))
    config_base['manifest']['$OUTPUT_DIR'] = output_dir
    config_base['inputs'] = {
        "current_clamp_1": {
            "input_type": "current_clamp",
            "module": "IClamp",
            "node_set": "biophys_cells",
            "amp": 0.1500,
            "delay": 500.0,
            "duration": 500.0
        },
        "current_clamp_2": {
            "input_type": "current_clamp",
            "module": "IClamp",
            "node_set": "biophys_cells",
            "amp": 0.1750,
            "delay": 1500.0,
            "duration": 500.0
        },
        "current_clamp_3": {
            "input_type": "current_clamp",
            "module": "IClamp",
            "node_set": "biophys_cells",
            "amp": 0.2000,
            "delay": 2500.0,
            "duration": 500.0
        }
    }

    conf = bionet.Config.from_dict(config_base, validate=True)
    conf.build_env()

    graph = bionet.BioNetwork.from_config(conf)
    sim = bionet.BioSimulator.from_config(conf, network=graph)
    sim.run()

    save_data('iclamp', output_dir)
    shutil.rmtree(output_dir)


def sim_xstim():
    output_dir = tempfile.mkdtemp()
    config_base = json.load(open('config_base.json'))
    config_base['manifest']['$OUTPUT_DIR'] = output_dir
    config_base['inputs'] = {
        "Extracellular_Stim": {
            "input_type": "lfp",
            "node_set": "all",
            "module": "xstim",
            "positions_file": "$COMPONENT_DIR/stimulations/485058595_0000.csv",
            "mesh_files_dir": "$COMPONENT_DIR/stimulations",
            "waveform": {
                "shape": "sin",
                "del": 500.0,
                "amp": 0.500,
                "dur": 2000.0,
                "freq": 8.0
            }
        }
    }

    conf = bionet.Config.from_dict(config_base, validate=True)
    conf.build_env()

    graph = bionet.BioNetwork.from_config(conf)
    sim = bionet.BioSimulator.from_config(conf, network=graph)
    sim.run()

    save_data('xstim', output_dir)
    shutil.rmtree(output_dir)


sim_virt()
# sim_iclamp()
# sim_xstim()
