'''
Test for waring raster to gems grid functions.

© Regents of the University of Minnesota. All rights reserved.
This software is released under an Apache 2.0 license. Further details about the Apache 2.0 license are available in the license.txt file.
'''
from gemsgrid.warp_raster_to_gems import *
import rasterio
import numpy as np
import pytest  # needed for tmp_path
import shutil

# input and validation raster data are located in s3 bucket
datadir = "https://s3.msi.umn.edu/gemsgrid-test-data/"

datadict = {
    0: {
        "filename": "pet_global_220711",
        "level": 0,
        "globalextent": True,
        "resamplingmethod": "nearest"
    },
    1: {
        "filename": "production",
        "level": 1,
        "globalextent": True,
        "resamplingmethod": "nearest"
    },
    2: {
        "filename": "chirps_v2_0_2022_05",
        "level": 2,
        "globalextent": False,
        "resamplingmethod": "nearest"
    },
    3: {
        "filename": "unprojected_wgs84",
        "level": 3,
        "globalextent": False,
        "resamplingmethod": "nearest"
    },
    4: {
        "filename": "LCMAP_CU_1985_V12_LCPRI_tile_70000-20000",
        "level": 4,
        "globalextent": False,
        "resamplingmethod": "nearest"
    },
    5: {
        "filename": "multi_band_sentinel",
        "level": 5,
        "globalextent": False,
        "resamplingmethod": "nearest"
    },
    6: {
        "filename": "lidar1",
        "level": 6,
        "globalextent": False,
        "resamplingmethod": "bilinear"
    }
}

@pytest.fixture
def set_raster_path(tmp_path):
    raster_path = tmp_path
    yield raster_path
    shutil.rmtree(raster_path, ignore_errors=True)

class TestWarpRasterToGems:
     # pytest's tmp_path is passed it. this is a pathlib object
     #    (e.g. POSIX compliant) temporary path. It is used in the
     #    the same way that any pathlib object is '/' is used to join
     #    with a file name, as below
    def test_warp_raster_to_gems(
        self,
        set_raster_path
    ):
        # create results arrays from the input data and verify if their shape and values match with validation arrays
        for key,value in datadict.items():
            #    resultrasterpath = MemoryFile()
            # this is joining the pathlib tmp_path with the file name for the warp
            resultrasterpath =  set_raster_path / '{0}_l{1}_result.tif'.format(value['filename'], str(value['level']))
            inrasterpath = datadir + "{}.tif".format(value["filename"])
            validrasterpath = datadir + "{0}_l{1}_valid.tif".format(value["filename"], str(value["level"]))
            warp_raster_to_gems(inrasterpath, resultrasterpath, value["level"], value["globalextent"],
                                value["resamplingmethod"], blocksize=512)
            result = rasterio.open(resultrasterpath).read()
            valid = rasterio.open(validrasterpath).read()
            assert np.allclose(result, valid, equal_nan=True), "Arrays are not equal"

class TestGenerateRasterGeoproperties:
    def test_generate_raster_geoproperties(self):
        # generate geoproperties and verify if they match with validation raster geoproperties
        for key,value in datadict.items():
            inrasterpath = datadir + "{}.tif".format(value["filename"])
            validrasterpath = datadir + "{0}_l{1}_valid.tif".format(value["filename"], str(value["level"]))
            with rasterio.open(inrasterpath) as raster:
                dst_transform, n_row, n_col = generate_raster_geoproperties(
                        raster,
                        level=value["level"],
                        globalextent=value["globalextent"]
                )
                valid = rasterio.open(validrasterpath)
                assert dst_transform == valid.transform, "Transform is not valid"
                assert n_row == valid.height, "Number of rows is not correct"
                assert n_col == valid.width, "Number of columns is not correct"
