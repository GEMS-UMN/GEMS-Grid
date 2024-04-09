'''
This module deals with methods to disaggreate vector files and placing on grid.

© Regents of the University of Minnesota. All rights reserved.
This software is released under an Apache 2.0 license. Further details about the Apache 2.0 license are available in the license.txt file.
'''
import rasterio
import geopandas as gpd
from rasterio import features
import numpy as np
from rasterio.crs import CRS
from rasterstats import zonal_stats
from gemsgrid.constants import grid_spec, levels_specs, ease_crs
from gemsgrid.grid_align import gems_grid_bounds
from shapely.geometry import box
import rasterio.mask
from gemsgrid.logConfig import logger

def open_and_project_vector (invectorpath):
    """
    Reads a shapefile (vector file) and projects it to target crs (EASE, epsg=6933)
        Parameters
        ----------
        invectorpath: str
            Describes the path of the input shapefile
        Returns
        -------
        gdf: GeoDataFrame
            Geopandas data frame projected to EASE
    """
    gdf = gpd.read_file(invectorpath)
    if gdf.crs.to_epsg() != ease_crs:
        gdf = gdf.to_crs(epsg=ease_crs)
    return gdf

def save_raster (outrasterpath, array, dst_transform, vectornodata=-9999):
    """
    Save raster to GeoTIFF file
        Parameters
        ----------
        outrasterpath: str
            Describes the path of the output raster file
        array: numpy array
            Data array to save
        dst_transform: Affine
            The transform for the raster dataset
        vectornodata: float or int (optional)
            Value to store "absence" of data; defaults to -9999
        Returns:
        ----------
        no return
        (saves the array to the outrasterpath defined above)
    """
    with rasterio.open(outrasterpath, "w",
                       compress="lzw",
                       driver="GTiff",
                       transform=dst_transform,
                       dtype=array.dtype,
                       count=1,
                       height=array.shape[0],
                       width=array.shape[1],
                       nodata=vectornodata,
                       crs=CRS.from_epsg(ease_crs)) as dst:
        dst.write(array, indexes=1)

def category_count (x):
    """Takes in array, returns its count of  x==1 values"""
    return np.count_nonzero(x==1)

def calculate_zonal_stats (row, array, affine, nodata, statistics):
    """
    Calculate zonal statistics for pixel count within a polygon
        Parameters
        ---------
        row: GeoDataFrame row
        array: numpy array
            Array from input raster
        affine: Affine
            The transform for the raster dataset
        nodata: int or float
            Assign explicitly nodata value to avoid warning
        statistics: str
            Defines statistics to summarize array data by geometry
            Supported : "sum", "count", "category_count"
        Return
        ------
        stats: int
            Pixel count
    """
    stats = zonal_stats(
        vectors=row["geometry"],
        raster=array,
        stats=["count", "sum"],
        add_stats = {"category_count": category_count},
        affine=affine,
        nodata=nodata)
    return stats[0][statistics]

def sum_weights (row, dict):
    """
    Calculate sum of weighs of present pixels (if all categories are present within a polygon, equals to 100%, otherwise is lower)
        Parameters
        ---------
        row: GeoDataFrame row
        dict: dictionary
            Describes conditions for masking and weight assigned to each category
        Return
        ------
        row: GeoDataFrame row
            Row with "sum_w" column value
    """
    row["sum_w"] = 0
    for key, value in dict.items():
        row["sum_w"] = row["sum_w"] + (np.where(row["count_{}".format(key)]>0, value[1], 0))
    return row

def add_category_var (row, var, weight, key):
    """
    Calculate class pixel values
        Parameters
        ---------
        row: GeoDataFrame row
        var: str
            Name of the GeoDataFrame column to disaggregate
        weight: percentage (0-100)
            Class weight
        key: int
            Class key from the dictionary
        Return
        ------
        GeoDataFrame row with value assigned to a given class
    """
    return row[var]*weight/row["sum_w"]/row["count_{}".format(key)]

def generate_raster_geoproperties (ease_gdf, level, globalextent):
    """"
    Get raster geoproperties from vector data opened as GeoDataFrame
        Parameters
        ---------
        ease_gdf: GeoDataFrame
            Geopandas data frame projected to epsg=6933
        level: int
            Valid GEMS level, options are: 0, 1, 2, 3, 4, 5, 6
        globalextent: boolean
            Specifies if vector data are global (globalextnet=True, otherwise globalextnet=False)
        Returns
        -------
        dictionary
            Contains the following keys and values:
                {
                "dst_transform": dst_transform,
                "n_row": n_row,
                "n_col": n_col
                }
            dst_transform: Affine
                The transform for the raster dataset
            n_row: int
                The dimensions of the raster dataset
            n_col: int
                The dimensions of the raster dataset
    """
    x_length = levels_specs[level]["x_length"]
    y_length = levels_specs[level]["y_length"]
    if globalextent == True:
        min_x = grid_spec["ease"]["min_x"]
        max_y = grid_spec["ease"]["max_y"]
        n_row = levels_specs[level]["n_row"]
        n_col = levels_specs[level]["n_col"]
    else:
        min_x_src, min_y_src, max_x_src, max_y_src = ease_gdf.total_bounds
        min_x, min_y, max_x, max_y = gems_grid_bounds((min_x_src, min_y_src, max_x_src, max_y_src),
                                                         level=level, source_crs=ease_gdf.crs)
        n_row = round((max_y - min_y)/y_length)
        n_col = round((max_x - min_x)/x_length)
    dst_transform = rasterio.Affine(x_length, 0.0, min_x, 0.0, -y_length, max_y)
    return {
        "dst_transform": dst_transform,
        "n_row": n_row,
        "n_col": n_col
    }

def generate_raster_geoproperties_and_maskarray (ease_gdf, inmaskpath, clip):
    """
    Get raster geoproperties from vector data and mask raster
        Parameters
        ----------
        ease_gdf: GeoDataFrame
            Geopandas data frame projected to epsg=6933
        inmaskpath: str
            Describes the path of the input mask file
        clip: boolean
            Specifies if mask raster has substantially larger extent compared to the input vector data
            and needs to be clipped (clip=True, otherwise clip=False)
        Returns
        -------
        dictionary
            Contains the following keys and values:
                {
                "dst_transform": dst_transform,
                "n_row": n_row,
                "n_col": n_col,
                "maskarray" : maskarray,
                "nodata": nodata
                }
            dst_transform: Affine
                The transform for the raster dataset
            n_row: int
                The dimensions of the raster dataset
            n_col: int
                The dimensions of the raster dataset
            maskarray: numpy array object
                Array from mask raster
            nodata: float or int
                Value to store "absence" of data
    """
    src = rasterio.open(inmaskpath)
    if clip == True:
        min_x_src, min_y_src, max_x_src, max_y_src = ease_gdf.total_bounds
        bbox = box(min_x_src, min_y_src, max_x_src, max_y_src)
        geo = gpd.GeoDataFrame({"geometry": bbox}, index=[0], crs=CRS.from_epsg(ease_crs))
        out_img, dst_transform = rasterio.mask.mask(dataset=src, shapes=geo["geometry"], crop=True)
        maskarray = out_img[0]
    else:
        maskarray = src.read(1)
        dst_transform = src.transform
    n_row = maskarray.shape[0]
    n_col = maskarray.shape[1]
    masknodata = src.nodata
    return {
        "dst_transform": dst_transform,
        "n_row": n_row,
        "n_col": n_col,
        "maskarray" : maskarray,
        "masknodata": masknodata
    }

def geom_to_array(ease_gdf, column, dst_transform, n_row, n_col, fill):
    """
    Supporting function to rasterize GeoDataFrame
        Parameters
        ----------
        ease_gdf: GeoDataFrame
            Geopandas data frame projected to EASE
        column: str
            Column name from the attribute table that needs to be disaggregated
        dst_transform: Affine
            The transform for the raster dataset
        n_row: int
            The dimensions of the raster dataset
        n_col: int
            The dimensions of the raster dataset
        fill: float or int
            Used as fill value for all areas not covered by input geometries
        Returns
        --------
        array: numpy array
            Rasterized array
    """
    # create tuples of geometry-value pairs, where value is the attribute value that needs to be rasterized
    geom_value = ((geom, value) for geom, value in zip(ease_gdf.geometry, ease_gdf[column]))
    # rasterize vector features using the shape and transform of the raster
    array = features.rasterize(geom_value,
                               out_shape=(n_row, n_col),
                               transform=dst_transform,
                               fill=fill,
                               all_touched=True)
    return array

def rasterize_unmasked (ease_gdf, var, dict_geoproperties, operation, vectornodata=-9999):
    """
    Rasterize GeoDataFrame
        Parameters
        ----------
        ease_gdf: GeoDataFrame
            Geopandas data frame projected to EASE
        var: str
            Column name from the attribute table that needs to be disaggregated
        dict_geoproperties: dictionary
            Contains the following keys and values:
                {
                "dst_transform": dst_transform,
                "n_row": n_row,
                "n_col": n_col
                }
            dst_transform: Affine
                The transform for the raster dataset
            n_row: int
                The dimensions of the raster dataset
            n_col: int
                The dimensions of the raster dataset
        operation: str
            Defines allocation rule
            operation == "repeat" - repeats polygon value to pixels
            operation == "divide" - divides polygon value by the number of pixels
        vectornodata: float or int (optional)
            Value to store "absence" of data; defaults to -9999
        Returns
        --------
        rasterized: numpy array
            Rasterized array
    """
    dst_transform = dict_geoproperties["dst_transform"]
    n_row = dict_geoproperties["n_row"]
    n_col = dict_geoproperties["n_col"]
    rasterized = geom_to_array(ease_gdf, var, dst_transform, n_row, n_col, vectornodata)
    # rasterized array from the line above is the final product if operation is "repeat"
    # block below is used for "divide" operation
    if operation == "divide":
        # operation is divide; get pixel count for shapes and update rasterized array
        ease_gdf["count"] = ease_gdf.apply(calculate_zonal_stats,
                                           array=rasterized,
                                           affine=dst_transform,
                                           nodata=vectornodata,
                                           statistics="count",
                                           axis=1)
        ease_gdf["{}_perpixel".format(var)] = ease_gdf[var] / ease_gdf["count"]
        rasterized = geom_to_array(ease_gdf, "{}_perpixel".format(var), dst_transform, n_row, n_col, vectornodata)
    return rasterized

def rasterize_masked (ease_gdf, var, dict_geoproperties, operation, vectornodata=-9999, categories_dict=None):
    """
    Rasterize GeoDataFrame
        Parameters
        ----------
        ease_gdf: GeoDataFrame
            Geopandas data frame projected to EASE
        var: str
            Column name from the attribute table that needs to be disaggregated
        dict_geoproperties: dictionary
            Contains the following keys and values:
                {
                "dst_transform": dst_transform,
                "n_row": n_row,
                "n_col": n_col,
                "maskarray": maskarray,
                "nodata": nodata
                }
            dst_transform: Affine
                The transform for the raster dataset
            n_row: int
                The dimensions of the raster dataset
            n_col: int
                The dimensions of the raster dataset
            maskarray: numpy array object
                Array from mask raster
            nodata: float or int
                Value to store "absence" of data
        operation: str
            Defines allocation rule
            operation == "repeat" - repeats polygon value to pixels
            operation == "divide" - divides polygon value by the number of pixels
            operation == "distribute" - distributes parent value based on proportions from a “suitability” mask
        vectornodata: float or int (optional)
            Value to store "absence" of data; defaults to -9999
        categories_dict: dictionary (required for "divide" and "repeat" operations)
            Describes conditions for masking and weight assigned to each category
            Note: is using operation = "repeat" only 1 category  with weight 100%  can be specified
            (even if it includes multiple classes)
            Usage examples:
                {1 : ["(mask == 1) | (mask == 5)", 100]}
                {1 : ["mask == 1", 100]}
            One or multiple categories with different weights can be provided for operation "divide":
            Usage examples:
                {1 : ["(mask == 1) | (mask == 5)", 100]} - only 1 category where pixel value is either 1 or 5
                {1 : ["mask == 1", 60], 2 : ["mask == 5", 20], 3 : ["mask == 6", 20] } - 3 categories with different
                weights (60%, 20%, and 20%)
                {1 : ["(mask > 0) & (mask <= 5)", 75], 2 : ["mask > 5", 25]} - two categories defined by a range of
                values
        Returns
        --------
        rasterized_masked: numpy array
            Rasterized array masked
    """
    if categories_dict is None:
        categories_dict = {}
    dst_transform = dict_geoproperties["dst_transform"]
    n_row = dict_geoproperties["n_row"]
    n_col = dict_geoproperties["n_col"]
    mask = dict_geoproperties["maskarray"]
    masknodata = dict_geoproperties["masknodata"]
    if operation == "repeat":
        rasterized = geom_to_array(ease_gdf, var, dst_transform, n_row, n_col, vectornodata)
        # keep only the pixels that meet the masking condition, otherwise reset to NoData
        # !!! Note: eval() function introduces potential security vulnerabilities
        rasterized_masked = np.where(eval(categories_dict[1][0]), rasterized, vectornodata)
    elif operation == "divide":
        overlap = np.zeros((mask.shape[0], mask.shape[1]))
        # Add GeoDataFrame columns with pixel count in each category
        for key, value in categories_dict.items():
            # !!! Note: eval() function introduces potential security vulnerabilities
            presence = np.where(eval(value[0]), 1, 0)
            if np.max(presence) == 0:
                logger.warning("Warning: mask does not contain data for the category {} : {}, "
                      "check your rules".format(key, value))
            overlap = overlap + presence
            ease_gdf["count_{}".format(key)] = ease_gdf.apply(calculate_zonal_stats,
                                                              array=presence,
                                                              affine=dst_transform,
                                                              nodata=masknodata,
                                                              statistics="category_count",
                                                              axis=1)
        if np.max(overlap) > 1:
            raise Exception("Some categories overlap, check your rules")
        # Sum up weights only for PRESENT classes within each polygon
        ease_gdf = ease_gdf.apply(sum_weights, dict=categories_dict, axis=1)
        ease_gdf["sum_w"].replace(0, np.nan)
        # generate masked "placeholder" array
        rasterized_masked = np.zeros((mask.shape[0], mask.shape[1]))
        # reset zeros to NoData value
        rasterized_masked[(rasterized_masked == 0)] = vectornodata
        for key, value in categories_dict.items():
            ease_gdf["{}_{}".format(var, key)] = ease_gdf.apply(add_category_var,
                                                            var=var,
                                                            weight=value[1],
                                                            key=key,
                                                            axis=1)
            rasterized = geom_to_array(ease_gdf, "{}_{}".format(var, key), dst_transform, n_row, n_col, vectornodata)
            # update weighted mask pixel values
            # !!! Note: eval() function introduces potential security vulnerabilities
            rasterized_masked = np.where(eval(value[0]), rasterized, rasterized_masked)
    elif operation == "distribute":
        mask = mask.astype(float)
        mask[mask == masknodata] = np.nan
        ease_gdf["sum"] = ease_gdf.apply(calculate_zonal_stats,
                                         array=mask,
                                         affine=dst_transform,
                                         nodata=np.nan,
                                         statistics="sum",
                                         axis=1)
        ease_gdf["ratio"] = ease_gdf[var] / ease_gdf["sum"]
        rasterized = geom_to_array(ease_gdf, "ratio", dst_transform, n_row, n_col, np.nan)
        rasterized_masked = rasterized * mask
    else:
        raise Exception("Operation is not supported; options are: repeat, divide, distribute")
    return rasterized_masked