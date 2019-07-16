from bmtk.utils.reports import CompartmentReport

report_expected = CompartmentReport('bio_14cells/expected/membrane_potential.h5', mode='r')
print(report_expected.populations)
