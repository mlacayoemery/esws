""""
This is a saved model run from natcap.invest.carbon.
Generated: 10/25/17 16:12:11
InVEST version: 3.3.3
"""

import natcap.invest.carbon


args = {
        u'carbon_pools_path': u'D:/Martin/Data/carbon/carbon_pools_samp.csv',
        u'discount_rate': 7.0,
        u'do_valuation': True,
        u'lulc_cur_path': u'D:/Martin/Data/Base_Data/Terrestrial/lulc_samp_cur.tif',
        u'lulc_cur_year': 2016,
        u'lulc_fut_path': u'D:/Martin/Data/Base_Data/Terrestrial/lulc_samp_fut.tif',
        u'lulc_fut_year': 2030,
        u'lulc_redd_path': u'D:/Martin/Data/carbon/lulc_samp_redd.tif',
        u'price_per_metric_ton_of_c': 43.0,
        u'rate_change': 0.0,
        u'workspace_dir': u'C:\\Users\\lacayoem/Documents/carbon_workspace',
}

if __name__ == '__main__':
    natcap.invest.carbon.execute(args)
