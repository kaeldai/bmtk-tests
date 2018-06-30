import sys
import os
import h5py
import json
import tempfile
import shutil
import numpy as np
import datetime
from optparse import OptionParser, BadOptionError, AmbiguousOptionError

from bmtk.simulator import bionet
from bmtk.utils.spike_trains import SpikesFile
from bmtk.utils.cell_vars import CellVarsFile

from neuron import h


try:
    pc = h.ParallelContext()
    MPI_size = int(pc.nhost())
    MPI_rank = int(pc.id())
    barrier = pc.barrier
except Exception as e:
    MPI_rank = 0
    MPI_size = 1
    def barrier(): pass


def save_data(sim_type, conn_type, output_dir):
    """Saves the expected results"""
    from bmtk import __version__ as bmtk_version
    from neuron import h
    import platform

    save_file = 'expected/sim_output_{}.h5'.format(sim_type)

    sample_data = h5py.File(save_file, 'w')
    root_group = sample_data['/']
    root_group.attrs['bmtk'] = bmtk_version
    root_group.attrs['date'] = str(datetime.datetime.now())
    root_group.attrs['python'] = '{}.{}'.format(*sys.version_info[0:2])
    root_group.attrs['NEURON'] = h.nrnversion()
    root_group.attrs['system'] = platform.system()
    root_group.attrs['arch'] = platform.machine()

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
    soma_grp.create_dataset('mapping/gids', data=soma_reports.h5['mapping/gids']) # data=[3])
    soma_grp.create_dataset('mapping/element_id', data=soma_reports.h5['mapping/element_id'])
    soma_grp.create_dataset('mapping/element_pos', data=soma_reports.h5['mapping/element_pos'])
    soma_grp.create_dataset('mapping/index_pointer', data=soma_reports.h5['mapping/index_pointer'])
    for var_name in soma_reports.variables:
        ds_name = '{}/data'.format(var_name)
        soma_grp.create_dataset(ds_name, data=soma_reports.h5[ds_name][-5000:, :])

    # compartmental report
    soma_reports = CellVarsFile(os.path.join(output_dir, 'full_cell_vars.h5'))
    soma_grp = sample_data.create_group('/compartmental')
    soma_grp.create_dataset('mapping/time', data=[2500.0, 3000.0, 0.1])
    soma_grp.create_dataset('mapping/gids', data=soma_reports.h5['mapping/gids']) # data=[3])
    soma_grp.create_dataset('mapping/element_id', data=soma_reports.h5['mapping/element_id'])
    soma_grp.create_dataset('mapping/element_pos', data=soma_reports.h5['mapping/element_pos'])
    soma_grp.create_dataset('mapping/index_pointer', data=soma_reports.h5['mapping/index_pointer'])
    for var_name in soma_reports.variables:
        ds_name = '{}/data'.format(var_name)
        soma_grp.create_dataset(ds_name, data=soma_reports.h5[ds_name][-5000:, :])

    # ecp data
    ecp_file = h5py.File(os.path.join(output_dir, 'ecp.h5'), 'r')
    ecp_grp = sample_data.create_group('/ecp')
    ecp_grp.create_dataset('data', data=ecp_file['data'][:, 0])
    ecp_grp.create_dataset('channel_id', data=ecp_file['channel_id'])


def get_inputs(input_type):
    """Used to build the "inputs" section of the config file"""
    input_type = input_type.lower()
    inputs_dict = {}
    if input_type == 'virt':
        inputs_dict = {
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

    elif input_type == 'iclamp':
        inputs_dict = {
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

    elif input_type == 'xstim':
        inputs_dict = {
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

    else:
        raise Exception('Unknown input type {} (options: virt, iclamp, xstim'.format(input_type))

    return inputs_dict

def get_network_path(conn_type):
    """Used to determine the path of the network being tested"""
    conn_type == conn_type.lower()
    if conn_type == 'nsyns':
        return 'network'

    elif conn_type == 'sections':
        return 'network_secs'

    else:
        raise Exception('Unknown conn_type {} (options: nsyns, secs)'.format(conn_type))


def get_expected_results(input_type, conn_type):
    """Gets the precomputed results based on the type of input and network"""
    return 'expected/sim_output_{}.h5'.format(input_type)


def test_bionet(input_type='virt', conn_type='nsyns', capture_output=True, tol=1e-05):
    print('Testing BioNet with {} inputs and {} synaptic connections'.format(input_type, conn_type))

    output_dir = 'output' if capture_output else tempfile.mkdtemp()
    config_base = json.load(open('config_base.json'))
    config_base['manifest']['$OUTPUT_DIR'] = output_dir
    config_base['inputs'] = get_inputs(input_type)
    config_base['manifest']['$NETWORK_DIR'] = os.path.join('$BASE_DIR', get_network_path(conn_type))

    conf = bionet.Config.from_dict(config_base, validate=True)
    conf.build_env()

    net = bionet.BioNetwork.from_config(conf)
    sim = bionet.BioSimulator.from_config(conf, net)
    sim.run()
    barrier()

    if MPI_rank == 0:
        print('Verifying output.')
        expected_file = get_expected_results(input_type, conn_type)

        # Check spikes file
        assert (SpikesFile(os.path.join(output_dir, 'spikes.h5')) == SpikesFile(expected_file))

        # soma reports
        soma_report_expected = CellVarsFile(expected_file, h5_root='/soma')
        soma_reports = CellVarsFile(os.path.join(output_dir, 'soma_vars.h5'))
        t_window = soma_report_expected.t_start, soma_report_expected.t_stop
        assert (soma_report_expected.dt == soma_reports.dt)
        assert (soma_report_expected.gids == soma_reports.gids)
        assert (soma_report_expected.variables == soma_reports.variables)
        for gid in soma_report_expected.gids:
            assert (soma_reports.compartment_ids(gid) == soma_report_expected.compartment_ids(gid)).all()
            for var in soma_report_expected.variables:
                assert (np.allclose(soma_reports.data(var, gid, time_window=t_window), soma_report_expected.data(var, gid),
                                    tol))

        # Compartmental reports
        compart_report_exp = CellVarsFile(expected_file, h5_root='/compartmental')
        compart_report = CellVarsFile(os.path.join(output_dir, 'full_cell_vars.h5'))
        t_window = compart_report_exp.t_start, compart_report_exp.t_stop
        assert (compart_report_exp.dt == compart_report.dt)
        assert (compart_report_exp.variables == compart_report.variables)
        for gid in compart_report_exp.gids:
            assert ((compart_report.compartment_ids(gid) == compart_report_exp.compartment_ids(gid)).all())
            for var in compart_report_exp.variables:
                assert (np.allclose(compart_report.data(var, gid, time_window=t_window, compartments='all'),
                                    compart_report_exp.data(var, gid, compartments='all'), tol))

        # ecp
        ecp_report = h5py.File(os.path.join(output_dir, 'ecp.h5'), 'r')
        ecp_report_exp = h5py.File(expected_file, 'r')
        ecp_grp_exp = ecp_report_exp['/ecp']
        assert(np.allclose(np.array(ecp_report['/data'][:, 0]), np.array(ecp_grp_exp['data']), tol))

    barrier()
    bionet.nrn.quit_execution()


def rebuild_expected(input_type='virt', conn_type='nsyns'):
    assert(MPI_size == 1)
    print('Building results for {} inputs and {} synaptic connections'.format(input_type, conn_type))

    output_dir = tempfile.mkdtemp()
    config_base = json.load(open('config.base.json'))
    config_base['manifest']['$OUTPUT_DIR'] = output_dir
    config_base['inputs'] = get_inputs(input_type)
    config_base['manifest']['$NETWORK_DIR'] = os.path.join('$BASE_DIR', get_network_path(conn_type))

    conf = bionet.Config.from_dict(config_base, validate=True)
    conf.build_env()

    net = bionet.BioNetwork.from_config(conf)
    sim = bionet.BioSimulator.from_config(conf, net)
    sim.run()

    save_data(sim_type=input_type, conn_type=conn_type, output_dir=output_dir)
    shutil.rmtree(output_dir)


def convert_nsyns():
    output_dir = 'output'
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

    config_base['reports'] = {
        'save_synapses': {
            'cells': 'all',
            'module': 'save_synapses',
            'network_dir': 'network_secs'
        }
    }

    conf = bionet.Config.from_dict(config_base, validate=True)
    conf.build_env()

    net = bionet.BioNetwork.from_config(conf)
    sim = bionet.BioSimulator.from_config(conf, net)
    sim.run()


class PassThroughOptionParser(OptionParser):
    def error(self, msg):
        pass

    def _process_args(self, largs, rargs, values):
        while rargs:
            try:
                OptionParser._process_args(self, largs, rargs, values)
            except (BadOptionError, AmbiguousOptionError), e:
                largs.append(e.opt_str)


if __name__ == '__main__':
    parser = PassThroughOptionParser(usage="Usage: python test_bionet [options] [rebuild]")
    parser.add_option('-i', '--input', dest='input_type', type='string', default='virt',
                      help='type of input to simulate against (virt, iclamp, xstim).')
    parser.add_option('-c', '--connections', dest='conn_type', type='string',  default='nsyns',
                      help="type of synpatic connections (nsyns, sections).")
    parser.add_option('--suppress-output', dest='capture_output', action='store_false', default=True,
                      help='do not save output.')

    options, args = parser.parse_args()
    if __file__ in args:
        args = args[args.index(__file__)+1:]

    if not args:
        test_bionet(input_type=options.input_type, conn_type=options.conn_type, capture_output=options.capture_output)

    if 'rebuild' in args:
        rebuild_expected(input_type=options.input_type, conn_type=options.conn_type)

    if 'convert' in args:
        convert_nsyns()
