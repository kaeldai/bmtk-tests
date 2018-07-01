import os
import sys
import datetime
import h5py
import tempfile
import json
import nest
import numpy as np
from optparse import OptionParser, BadOptionError, AmbiguousOptionError

from bmtk.simulator import pointnet
from bmtk.simulator.pointnet.pyfunction_cache import py_modules
from bmtk.utils.spike_trains import SpikesFile

#def process_model(model_type, node, dynamics_params):
#    return nest.Create(model_type, 1, dynamics_params)

def save_data(sim_type, conn_type, output_dir):
    """Saves the expected results"""
    from bmtk import __version__ as bmtk_version
    import platform

    if not os.path.exists('expected'):
        os.mkdir('expected')

    save_file = 'expected/sim_output_{}.h5'.format(sim_type)

    sample_data = h5py.File(save_file, 'w')
    root_group = sample_data['/']
    root_group.attrs['bmtk'] = bmtk_version
    root_group.attrs['date'] = str(datetime.datetime.now())
    root_group.attrs['python'] = '{}.{}'.format(*sys.version_info[0:2])
    root_group.attrs['NEST'] = nest.version()
    root_group.attrs['system'] = platform.system()
    root_group.attrs['arch'] = platform.machine()

    # spikes data
    input_spikes = SpikesFile(os.path.join(output_dir, 'spikes.h5'))
    spikes_df = input_spikes.to_dataframe()
    sample_data.create_dataset('/spikes/gids', data=np.array(spikes_df['gids']))
    sample_data.create_dataset('/spikes/timestamps', data=np.array(spikes_df['timestamps']))
    sample_data['/spikes/gids'].attrs['sorting'] = 'time'


def gaussianLL(edge_props, source_node, target_node):
    return edge_props['syn_weight']

def process_model(model_type, node, dynamics_params):
    return nest.Create(model_type, 1, dynamics_params)


def get_expected_results(input_type):
    """Gets the precomputed results based on the type of input and network"""
    return 'expected/sim_output_{}.h5'.format(input_type)

def get_network_path(net_type='batched'):
    """Used to determine the path of the network being tested"""
    net_type == net_type.lower()
    if net_type == 'batched':
        return 'network'

    elif net_type == 'individual':
        return 'network_indv'

    else:
        raise Exception('Unknown network type {}.'.format(net_type))


def rebuild_expected(input_type='virt', conn_type='nsyns'):
    print('Building results')
    output_dir = tempfile.mkdtemp()

    config_base = json.load(open('config.json'))
    config_base['manifest']['$OUTPUT_DIR'] = output_dir
    configure = pointnet.Config.from_dict(config_base)
    configure.build_env()

    network = pointnet.PointNetwork.from_config(configure)
    py_modules.add_synaptic_weight('gaussianLL', gaussianLL)

    sim = pointnet.PointSimulator.from_config(configure, network)
    sim.run()
    save_data(sim_type=input_type, conn_type=conn_type, output_dir=output_dir)


def test_pointnet(input_type='virt', net_type='batched', capture_output=True, tol=1e-05):
    output_dir = 'output' if capture_output else tempfile.mkdtemp()
    config_base = json.load(open('config.json'))
    config_base['manifest']['$OUTPUT_DIR'] = output_dir
    # config_base['inputs'] = get_inputs(input_type)
    config_base['manifest']['$NETWORK_DIR'] = get_network_path(net_type) # os.path.join('$BASE_DIR', 'network')


    configure = pointnet.Config.from_dict(config_base)
    # configure = pointnet.Config.from_json('config.json')
    configure.build_env()

    network = pointnet.PointNetwork.from_config(configure)
    py_modules.add_cell_processor('process_model', process_model)
    # py_modules.add_synaptic_weight('gaussianLL', gaussianLL)

    sim = pointnet.PointSimulator.from_config(configure, network)
    sim.run()

    expected_file = get_expected_results(input_type)

    # Check spikes file
    assert (SpikesFile(os.path.join(output_dir, 'spikes.h5')) == SpikesFile(expected_file))
    # assert (spike_files_equal(configure['output']['spikes_file_csv'], 'expected/spikes.csv'))


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
    parser.add_option('-n', '--network_type', dest='net_type', type='string',  default='batched',
                      help="process for building networks (batched, individual).")
    parser.add_option('--suppress-output', dest='capture_output', action='store_false', default=True,
                      help='do not save output.')

    options, args = parser.parse_args()
    if __file__ in args:
        args = args[args.index(__file__)+1:]

    if not args:
        test_pointnet(input_type=options.input_type, net_type=options.net_type, capture_output=options.capture_output)

    if 'rebuild' in args:
        rebuild_expected(input_type=options.input_type, net_type=options.net_type)
