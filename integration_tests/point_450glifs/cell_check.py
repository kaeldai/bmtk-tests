import nest

model_para_dict = [True, False, False]

params = {
    "spike_dependent_threshold": model_para_dict[0],
    "after_spike_currents": model_para_dict[1],
    "adapting_threshold": model_para_dict[2],
}

nest.Create("glif_psc", params=params)
nest.Simulate(1000.)
