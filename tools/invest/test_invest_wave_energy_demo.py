""""
This is a saved model run from natcap.invest.wave_energy.wave_energy.
Generated: 11/06/17 11:25:11
InVEST version: 3.3.3
"""

import natcap.invest.wave_energy.wave_energy
import os

args = {
        u'analysis_area_uri': u'West Coast of North America and Hawaii',
        u'aoi_uri': u'~/workspace/data/WaveEnergy/input/AOI_WCVI.shp',
        u'dem_uri': u'~/workspace/data/Base_Data/Marine/DEMs/global_dem.tif',
        u'land_gridPts_uri': u'~/workspace/data/WaveEnergy/input/LandGridPts_WCVI.csv',
        u'machine_econ_uri': u'~/workspace/data/WaveEnergy/input/Machine_Pelamis_Economic.csv',
        u'machine_param_uri': u'~/workspace/data/WaveEnergy/input/Machine_Pelamis_Parameter.csv',
        u'machine_perf_uri': u'~/workspace/data/WaveEnergy/input/Machine_Pelamis_Performance.csv',
        u'number_of_machines': u'28',
        u'valuation_container': True,
        u'wave_base_data_uri': u'~/workspace/data/WaveEnergy/input/WaveData',
        u'workspace_dir': u'/tmp/wave_energy_workspace',
}

if __name__ == '__main__':
    for k in args.keys():
        try:
            args[k] = os.path.expanduser(args[k])

        except AttributeError:
            continue

    natcap.invest.wave_energy.wave_energy.execute(args)
