import sys
import os
import json
import tempfile
import shutil
import pandas as pd
import numpy as np

from bmtk.simulator import popnet
from optparse import OptionParser, BadOptionError, AmbiguousOptionError


def test_popnet(capture_output=True):
    output_dir = 'output' if capture_output else tempfile.mkdtemp()
    config_base = json.load(open('config.json'))
    config_base['manifest']['$OUTPUT_DIR'] = output_dir
    configure = popnet.Config.from_dict(config_base)
    network = popnet.PopNetwork.from_config(configure)
    sim = popnet.PopSimulator.from_config(configure, network)
    sim.run()

    output_df = pd.read_csv(configure['output']['rates_file'], sep=' ', names=['id', 'time', 'rates'])
    output_groups = output_df.groupby(by=['id'])

    expected_df = pd.read_csv('expected/rates.csv', sep=' ', names=['id', 'time', 'rates'])
    expected_groups = expected_df.groupby(by=['id'])

    assert(set(expected_groups.groups.keys()) == set(output_groups.groups.keys()))
    for e_keys in expected_groups.groups.keys():
        expected_rates = np.array(output_df.iloc[output_groups.groups[e_keys]]['rates'])
        output_rates = np.array(expected_df.iloc[output_groups.groups[e_keys]]['rates'])
        np.allclose(expected_rates, output_rates)


def rebuild_results():
    output_dir = tempfile.mkdtemp()
    config_base = json.load(open('config.json'))
    config_base['manifest']['$OUTPUT_DIR'] = output_dir
    configure = popnet.Config.from_dict(config_base)
    network = popnet.PopNetwork.from_config(configure)
    sim = popnet.PopSimulator.from_config(configure, network)
    sim.run()

    if not os.path.exists('expected'):
        os.mkdir('expected')

    shutil.move(configure['output']['rates_file'], 'expected/rates.csv')


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
    parser = PassThroughOptionParser(usage="Usage: python test_popnet.py [options] [rebuild]")
    parser.add_option('--suppress-output', dest='capture_output', action='store_false', default=True,
                      help='do not save output.')

    options, args = parser.parse_args()
    if __file__ in args:
        args = args[args.index(__file__)+1:]

    if not args:
        test_popnet()

    if 'rebuild' in args:
        rebuild_results()
