import sys
import os
import json
import h5py
import numpy as np
import pandas as pd
from bmtk.utils.reports import SpikeTrains
from bmtk.utils.reports import CompartmentReport


def check_spikes(actual_h5, expected_h5):
    assert(SpikeTrains.from_sonata(actual_h5) == SpikeTrains.from_sonata(expected_h5))


def check_compartmental_report(actual_h5, expected_h5, tol=1e-05):
    report_expected = CompartmentReport(expected_h5, mode='r')
    report_actual = CompartmentReport(actual_h5, mode='r')
    t_window = report_expected.tstart(), report_expected.tstop()
    assert(report_expected.dt() == report_actual.dt())
    assert(set(report_expected.node_ids()) == set(report_actual.node_ids()))
    assert(set(report_expected.populations) == set(report_actual.populations))
    for pop in report_expected.populations:
        for node_id in report_expected[pop].node_ids():
            assert(np.all(report_expected[pop].element_ids(node_id) == report_actual[pop].element_ids(node_id)))
            assert(np.all(report_expected[pop].element_pos(node_id) == report_actual[pop].element_pos(node_id)))
            assert(np.allclose(report_expected[pop].data(node_id=node_id, time_window=t_window),
                              report_actual[pop].data(node_id=node_id, time_window=t_window), tol))


def check_ecp(actual_h5, expected_h5, tol=1e-05):
    ecp_report = h5py.File(actual_h5, 'r')
    ecp_report_exp = h5py.File(expected_h5, 'r')
    ecp_grp_exp = ecp_report_exp['/']
    assert (np.allclose(np.array(ecp_report['/ecp/data'][()]), np.array(ecp_grp_exp['/ecp/data'][()]), tol))


def check_rates(expected_csv, actual_csv):
    expected_df = pd.read_csv(expected_csv, names=['node_ids', 'rates'], sep=' ')
    actual_df = pd.read_csv(actual_csv, names=['node_ids', 'rates'], sep=' ')
    assert(expected_df.equals(actual_df))


def check_filternet_rates(expected_csv, actual_csv, pass_rate=.70):
    expected_df = pd.read_csv(expected_csv, names=['node_ids', 'times', 'rates'], sep=' ')
    actual_df = pd.read_csv(actual_csv, names=['node_ids', 'times', 'rates'], sep=' ')

    assert(len(actual_df['rates']) == len(expected_df['rates']))
    assert(len(actual_df['node_ids'].unique()) == len(expected_df['node_ids'].unique()))

    passed = 0
    for node_id in expected_df['node_ids'].unique():
        expected_rates = expected_df[expected_df['node_ids'] == node_id]['rates']
        actual_rates = actual_df[actual_df['node_ids'] == node_id]['rates']

        if np.abs(actual_rates.mean() - expected_rates.mean()) < expected_rates.std()/np.sqrt(expected_rates.mean()):
            passed += 1
    print('{}% of the cells fell within the standard error'.format(passed/float(len(expected_df['node_ids'].unique()))))
    assert(passed/float(len(expected_df['node_ids'].unique())) > pass_rate)



if __name__ == '__main__':
    input_path = sys.argv[-1]
    sim_path = os.path.abspath(os.path.dirname(input_path))

    files_data = json.load(open(input_path))
    for fd in files_data:
        ftype = fd['type']
        fname = fd['name']
        expected_file = os.path.join(sim_path, 'expected', fname)
        actual_file = os.path.join(sim_path, 'output', fname)

        print('Checking {}'.format(fname))
        if ftype == 'spikes':
            check_spikes(actual_file, expected_file)

        elif ftype == 'compartmental':
            check_compartmental_report(actual_file, expected_file)

        elif ftype == 'ecp':
            check_ecp(actual_file, expected_file)

        elif ftype == 'rates':
            check_rates(actual_file, expected_file)

        elif ftype == 'filternet_rates':
            check_filternet_rates(actual_file, expected_file)

        else:
            print('Unknown file type: {}'.format(ftype))
