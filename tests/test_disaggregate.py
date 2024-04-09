'''
Module used for testing the disaggreation functions.

© Regents of the University of Minnesota. All rights reserved.
This software is released under an Apache 2.0 license. Further details about the Apache 2.0 license are available in the license.txt file.
'''
from gemsgrid.processing_tools.disaggregate import disaggregate
import rasterio
import numpy as np
import pytest
import shutil

# input and validation raster data are located in s3 bucket
datadir = "https://s3.msi.umn.edu/gemsgrid-test-data/disaggregation-test-data/"

test_cases = {
    1 : {
        "input_type": "vector_unmasked",
        "outrasterpath": "mn_county_ag_value_unmasked_repeat.tif",
        "operation": "repeat",
        "invectorpath": "mn_county_ag_value.zip",
        "var": "valueperac",
        "target_level": 4,
        "globalextent": False
    },
    2 : {
        "input_type": "vector_unmasked",
        "outrasterpath": "mn_county_ag_value_unmasked_divide.tif",
        "operation": "divide",
        "invectorpath": "mn_county_ag_value.zip",
        "var": "totalvalue",
        "target_level": 4,
        "globalextent": False
    },
    3 : {
        "input_type": "vector_masked",
        "outrasterpath": "mn_county_ag_value_masked_repeat.tif",
        "operation": "repeat",
        "invectorpath": "mn_county_ag_value.zip",
        "var": "valueperac",
        "inmaskpath": "LCMAP_CU_2017_V12_LCPRI_l4.tif",
        "categories_dict": {1: ["mask==2", 100]},
        "clip": True
    },
    4 : {
        "input_type": "vector_masked",
        "outrasterpath": "mn_county_ag_value_masked_divide_1categ.tif",
        "operation": "divide",
        "invectorpath": "mn_county_ag_value.zip",
        "var": "totalvalue",
        "inmaskpath": "LCMAP_CU_2017_V12_LCPRI_l4.tif",
        "clip": True,
        "categories_dict": {1: ["mask==2", 100]}
    },
    5 : {
        "input_type" : "vector_masked",
        "outrasterpath": "mn_county_ag_value_masked_divide_2categ.tif",
        "operation": "divide",
        "invectorpath" : "mn_county_ag_value.zip",
        "var" : "totalvalue",
        "inmaskpath" : "LCMAP_CU_2017_V12_LCPRI_l4.tif",
        "clip" : True,
        "categories_dict" : {1 : ["mask == 2", 97], 2 : ["mask == 3", 3]}
    },
    6 : {
        "input_type": "vector_masked",
        "outrasterpath": "mn_county_ag_value_distributed.tif",
        "operation": "distribute",
        "invectorpath": "mn_county_ag_value.zip",
        "var": "totalvalue",
        "inmaskpath": "mn_crop_productivity.tif",
        "clip": True
    },
    7 : {
        "input_type" : "raster_unmasked",
        "outrasterpath": "asia_production_perhectare_l2_unmasked_repeat.tif",
        "operation": "repeat",
        "inrasterpath" : "asia_production_perhectare_l1.tif",
        "source_level" : 1
    },
    8 : {
        "input_type" : "raster_unmasked",
        "outrasterpath": "asia_production_total_l2_unmasked_divide.tif",
        "operation": "divide",
        "inrasterpath" : "asia_production_total_l1.tif",
        "source_level" : 1
    },
    9 : {
        "input_type" : "raster_masked",
        "outrasterpath": "asia_production_perhectare_l2_masked_repeat.tif",
        "operation": "repeat",
        "inrasterpath" : "asia_production_perhectare_l1.tif",
        "source_level" : 1,
        "inmaskpath": "GFSAD1KCM.2010.001.2016348142550_l2.tif",
        "categories_dict": {1 : ["(mask == 1) | (mask == 2)| (mask == 3) | (mask == 4) | (mask == 5)", 100]}
    },
    10 : {
        "input_type" : "raster_masked",
        "outrasterpath": "asia_production_total_l2_masked_divide_1categ.tif",
        "operation": "divide",
        "inrasterpath" : "asia_production_total_l1.tif",
        "source_level" : 1,
        "inmaskpath": "GFSAD1KCM.2010.001.2016348142550_l2.tif",
        "categories_dict": {1 : ["(mask == 1) | (mask == 2)| (mask == 3) | (mask == 4) | (mask == 5)", 100]}
    },
    11 : {
        "input_type" : "raster_masked",
        "outrasterpath": "asia_production_total_l2_masked_divide_2categ.tif",
        "operation": "divide",
        "inrasterpath" : "asia_production_total_l1.tif",
        "source_level" : 1,
        "inmaskpath": "GFSAD1KCM.2010.001.2016348142550_l2.tif",
        "categories_dict": {1 : ["(mask == 1) | (mask == 2)", 40], 2: ["(mask == 3) | (mask == 4) | (mask == 5)", 60]}
    },
    12 : {
        "input_type" : "raster_masked",
        "outrasterpath": "asia_production_total_l2_distributed.tif",
        "operation": "distribute",
        "inrasterpath" : "asia_production_total_l1.tif",
        "source_level" : 1,
        "inmaskpath": "AWCh2_M_sl6_250m_ll_l2.tif"
    }
}

@pytest.fixture
def set_raster_path(tmp_path):
    raster_path = tmp_path
    yield raster_path
    shutil.rmtree(raster_path, ignore_errors=True)

class TestDisaggregate:
    def test_disaggregate(
            self,
            set_raster_path
    ):
        for key, arguments in test_cases.items():
            validrasterpath = datadir + arguments["outrasterpath"]
            arguments["outrasterpath"] = set_raster_path / arguments["outrasterpath"]
            if "invectorpath" in arguments:
                arguments["invectorpath"] = 'zip+' + datadir + arguments["invectorpath"]
            if "inrasterpath" in arguments:
                arguments["inrasterpath"] = datadir + arguments["inrasterpath"]
            if "inmaskpath" in arguments:
                arguments["inmaskpath"] = datadir + arguments["inmaskpath"]
            disaggregate(**arguments)
            result = rasterio.open(set_raster_path / arguments["outrasterpath"]).read()
            print(f'validrasterpath: {validrasterpath}')
            valid = rasterio.open(validrasterpath).read()
            assert np.allclose(result, valid, equal_nan=True), \
                "Arrays are not equal, check test case {}".format(key)
