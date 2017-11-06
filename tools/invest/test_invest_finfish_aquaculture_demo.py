""""
This is a saved model run from natcap.invest.finfish_aquaculture.finfish_aquaculture.
Generated: 11/06/17 10:59:46
InVEST version: 3.3.3
"""

import natcap.invest.finfish_aquaculture.finfish_aquaculture
import os

args = {
        u'discount': 0.000192,
        u'do_valuation': True,
        u'farm_ID': u'FarmID',
        u'farm_op_tbl': u'~/workspace/data/Aquaculture/Input/Farm_Operations.csv',
        u'ff_farm_loc': u'~/workspace/data/Aquaculture/Input/Finfish_Netpens.shp',
        u'frac_p': 0.3,
        u'g_param_a': 0.038,
        u'g_param_a_sd': 0.005,
        u'g_param_b': 0.6667,
        u'g_param_b_sd': 0.05,
        u'g_param_tau': 0.08,
        u'num_monte_carlo_runs': 1000,
        u'outplant_buffer': 3,
        u'p_per_kg': 2.25,
        u'use_uncertainty': True,
        u'water_temp_tbl': u'~/workspace/data/Aquaculture/Input/Temp_Daily.csv',
        u'workspace_dir': u'/tmp/aquaculture_workspace',
}

if __name__ == '__main__':
    for k in args.keys():
        try:
            args[k] = os.path.expanduser(args[k])

        except AttributeError:
            continue

    natcap.invest.finfish_aquaculture.finfish_aquaculture.execute(args)
