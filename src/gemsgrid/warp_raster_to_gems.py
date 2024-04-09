'''
Warping raster to gems grid functions.

© Regents of the University of Minnesota. All rights reserved.
This software is released under an Apache 2.0 license. Further details about the Apache 2.0 license are available in the license.txt file.
'''
from gemsgrid.constants import grid_spec, levels_specs, ease_crs
from gemsgrid.grid_align import gems_grid_bounds
from gemsgrid.dggs.checks import check_level
import rasterio
from rasterio.crs import CRS
from rasterio.enums import Resampling
from rasterio import shutil as rio_shutil
from rasterio.vrt import WarpedVRT
import pyproj
from gemsgrid.logConfig import logger

def generate_raster_geoproperties (dataset, level, globalextent):
    """
    Get raster geoproperties to project raster to GEMS
        Arguments
        ----------
        dataset : opened raster dataset object
            Raster opened with rasterio
        level: int
            Valid GEMS level, options are: 0, 1, 2, 3, 4, 5, 6
        globalextent: boolean
            Specifies if raster is global (globalextnet=True, otherwise globalextnet=False)
        Returns
        -------
        dst_transform: Affine
            The transform for the virtual dataset
        n_row: int
            The dimensions of the virtual dataset
        n_col: int
            The dimensions of the virtual dataset
    """
    logger.debug("Source dataset geoproperties are the following: ")
    logger.debug("Transform is {}".format(dataset.transform))
    logger.debug("Width is {}, height is {}".format(dataset.width, dataset.height))
    logger.debug("Coordinate system is {}".format(dataset.crs))
    if dataset.crs == None:
        raise Exception("Unknown coordinate system")
    # define pixel resolution from gemsgrid spec
    x_length = levels_specs[level]['x_length']
    y_length = levels_specs[level]['y_length']
    # define n_row and n_col
    if globalextent == True:
        min_x = grid_spec['ease']['min_x']
        max_y = grid_spec['ease']['max_y']
        n_row = levels_specs[level]['n_row']
        n_col = levels_specs[level]['n_col']
    else:
        min_x_src, min_y_src, max_x_src, max_y_src = dataset.bounds
        min_x, min_y, max_x, max_y = gems_grid_bounds((min_x_src, min_y_src, max_x_src, max_y_src),
                                                         level=level, source_crs=dataset.crs)
        n_row = round((max_y - min_y) / y_length)
        n_col = round((max_x - min_x) / x_length)
    # create Affine object
    dst_transform = rasterio.Affine(x_length, 0.0, min_x, 0.0, -y_length, max_y)
    return dst_transform, n_row, n_col

def warp_raster_to_gems(inrasterpath, outrasterpath, level, globalextent, resamplingmethod, nodata=None,
                        tolerance=0.125, blocksize=256):
    """
    Project raster file to GEMS grid
        Arguments
        ----------
        inrasterpath : str
            Describes the path of the input file
        outrasterpath : str
            Describes the path of the output file
        level: int
            Valid GEMS level, options are: 0, 1, 2, 3, 4, 5, 6
        globalextent: boolean
            Specifies if raster is global (globalextnet=True, otherwise globalextnet=False)
        resamplingmethod: str
            Specifies resampling method.
            Curently supports all methods available from rasterio.enums.Resampling:
            ("nearest", "bilinear", "cubic", "cubic_spline", "lanczos", "average",
             "mode", "max", "min", "med", "q1", "q3", "sum", "rms")
        nodata : float (optional)
            Nodata value for the virtual dataset.
            Defaults to the NoData value of the source dataset.
            If missing, needs to be assigned to a numerical value here
        tolerance : float (optional)
            The maximum error tolerance in input pixels when approximating the warp transformation.
            Defaults to 0.125, or one-eigth of a pixel.
            Consider changing it to a smaller value for high resolution datasets.
        blocksize: int (optional)
            Sets the tile width and height in pixels. Options are: 256, 512, 1024, 2048, 4096.
            Defaults to 256
        Returns
            -------
            no return
            (saves the disaggregated output file to the outfilepath defined above)
    """
    if not check_level(level):
        raise Exception("Invalid grid level; options are: 0, 1, 2, 3, 4, 5, 6")
    if resamplingmethod not in [x for x in dir(Resampling) if not x.startswith('__')]:
        raise Exception("Resampling method is not supported, check available rasterio methods")
    if blocksize not in [256, 512, 1024, 2048, 4096]:
        raise Exception("Invalid COG block size; options are: 256, 512, 1024, 2048, 4096;  defaults to 256")
    with rasterio.open(inrasterpath) as src:
        dst_transform, n_row, n_col = generate_raster_geoproperties(src, level, globalextent)
        rs = getattr(Resampling, resamplingmethod)
        if nodata is None:
            if src.nodata is None:
                raise Exception("NoData is missing and needs to be specified")
            nodata = src.nodata
        # VRT options
        vrt_options = {
            "resampling": rs,
            "crs": CRS.from_epsg(ease_crs),
            "transform": dst_transform,
            "height": n_row,
            "width": n_col,
            "nodata": nodata,
            "tolerance": tolerance
        }
        logger.debug("VRT options are the following: ")
        logger.debug(vrt_options)
        with WarpedVRT(src, **vrt_options) as vrt:
            vrt.read()
            rio_shutil.copy(vrt, outrasterpath, driver="COG", compress="lzw", blocksize=blocksize,
                            overviews=None)
            logger.debug("Raster warped and saved")
