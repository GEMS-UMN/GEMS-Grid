'''
Functions for disaggregating rasters to finer spatial resolution.

© Regents of the University of Minnesota. All rights reserved.
This software is released under an Apache 2.0 license. Further details about the Apache 2.0 license are available in the license.txt file.
'''
import rasterio
import numpy as np
import scipy.ndimage
from rasterio.enums import Resampling
from rasterio.vrt import WarpedVRT
from rasterio.crs import CRS
from gemsgrid.constants import ease_crs, levels_specs
from gemsgrid.logConfig import logger

def open_raster (inrasterpath):
    """
    Read a raster GeoTIFF file and return an array and raster properties
        Parameters
        ----------
        inrasterpath: str
            Describes the path of the input file
        Returns
        -------
        dictionary
            Contains the following keys and values:
                {
                "array": array
                "transform": transform
                "nodata": nodata
                }
            array: numpy array object
                Array from raster
            transform: Affine
                The transform for the raster dataset
            nodata: float or int
                Value to store "absence" of data
    """
    with rasterio.open(inrasterpath) as dataset:
        data = dataset.read(1)
        return {
            "array" : data,
            "transform" : dataset.transform,
            "nodata" : dataset.nodata,
        }

def save_raster (outrasterpath, array, dst_transform, nodata):
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
        nodata: float or int
            Value to store "absence" of data
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
                  nodata=nodata,
                  crs=CRS.from_epsg(ease_crs)) as dst:
        dst.write(array, indexes=1)

def align_mask_bounds (inrasterpath, inmaskpath, refine_ratio):
    """
    Align GEMS mask to GEMS input raster (coarser level) to ensure proper nesting of children within parents
        Parameters
        ----------
        inrasterpath: str
            Describes the path of the input raster file
        inmaskpath: str
            Describes the path of the input mask file
        refine_ratio: int
            Upscale factor corresponds to the refine ratio between different levels
            Options are 4, 3, 3, 10, 10, 10
            e.g, if you are going from level 1 to level 2, refine_ratio=3
        Returns
        -------
        numpy array, mask NoData value
            Mask array aligned with the bounds of the input file that needs to be disaggregated
    """
    with rasterio.open(inrasterpath) as match:
        match.read(1)
        vrt_options = {
            "resampling": Resampling.nearest,
            "crs": match.crs,
            "transform": match.transform * match.transform.scale((1 / refine_ratio),(1 / refine_ratio)),
            "height": int(match.height * refine_ratio),
            "width": int(match.width * refine_ratio)}
        with rasterio.open(inmaskpath) as src:
            with WarpedVRT(src, **vrt_options) as vrt:
                return vrt.read(1), vrt.nodata

def create_weights_matrix (mask, categories_dict, refine_ratio):
    """
    Creates weights matrix
        Parameters
        ----------
        mask: numpy array
            Mask array aligned with the bounds of input file that needs to be disaggregated
        categories_dict: dictionary
            Describes conditions for masking and weight assigned to each category
        refine_ratio: int
            Upscale factor corresponds to the refine ratio between different levels
            Options are 4, 3, 3, 10, 10, 10
            e.g, if you are going from level 1 to level 2, refine_ratio=3
        Returns
        -------
        weights_matrix: numpy array
            Weights matrix array with parent pixel fractions (0 - 1) assigned to each child
    """
    # create "0" array to sum up weights for categories that are present in each parent
    sum_of_weights = np.zeros((int(mask.shape[0] / refine_ratio),
                               int(mask.shape[1] / refine_ratio)))
    overlap = np.zeros((mask.shape[0], mask.shape[1]))
    for key, value in categories_dict.items():
        # !!! Note: eval() function introduces potential security vulnerabilities
        presence = np.where(eval(value[0]), 1, 0)
        if np.max(presence) == 0:
            logger.warning("Warning: mask does not contain data for the category {} : {}, check your rules".format(key, value))
        overlap = overlap + presence
        # aggregate mask to coarser level by summing all valid pixels
        aggregated = presence.reshape(int(mask.shape[0] / refine_ratio),
                                      refine_ratio,
                                      int(mask.shape[1] / refine_ratio),
                                      refine_ratio).sum(axis=(1, 3))
        # if at least one child exists within a parent, retain its weight and add it to sum_of_weights array
        updated_weight = np.where(aggregated >= 1, value[1], 0)
        sum_of_weights = sum_of_weights + updated_weight
        aggregated = aggregated.astype(float)
        aggregated[aggregated == 0] = np.nan
        # expand the dictionary by adding array with aggregaed mask values
        value.append(aggregated)
    if np.max(overlap) > 1:
        raise Exception("Some categories overlap, check your rules")
    sum_of_weights[sum_of_weights == 0] = np.nan
    # create '0' array as a placeholder for weighted mask
    weights_matrix = np.zeros((mask.shape[0], mask.shape[1]))
    for key, value in categories_dict.items():
        # to find a child value, divide category weight by sum_of_weights and then by the number of children
        child_value = value[1] / sum_of_weights / value[2]
        # resample child value array back to original mask number of rows and columns
        child_value_res = scipy.ndimage.zoom(child_value, zoom=(refine_ratio, refine_ratio),
                                             order=0, mode="nearest", grid_mode=True)
        # assign children fraction only to children that meet the condition, the rest are 0
        # !!! Note: eval() function introduces potential security vulnerabilities
        child_value_res[~(eval(value[0]))] = 0
        # update weights matrix values
        weights_matrix = weights_matrix + child_value_res
    return weights_matrix

def scale_transform (src_transform, level):
    """
    Scale transfrom
    Parameters
        ----------
        src_transform: Affine
            The transform for the source raster dataset
        level: int
            Valid GEMS level of the original data, options are: 0, 1, 2, 3, 4, 5, 6
    Returns
        -------
        scaled_transform: Affine
            The transform for the source raster dataset
    """
    refine_ratio = levels_specs[level]["refine_ratio"]
    scaled_transform = src_transform * src_transform.scale((1 / refine_ratio), (1 / refine_ratio))
    return scaled_transform

def resample_unmasked(data_dict, level, operation):
    """
    Resample GEMS raster to finer level
        Parameters
        ----------
        data_dict: dictionary
            Contains the following keys and values:
                {
                "array": array
                "transform": transform
                "nodata": nodata
                }
            array: numpy array object
                Array from raster
            transform: Affine
                The transform for the raster dataset
            nodata: float or int
                Value to store "absence" of data
        level: int
            Valid GEMS level of the original data, options are: 0, 1, 2, 3, 4, 5, 6
        operation: str
            Defines allocation rule
            operation == "repeat" - repeats parent value to children
            operation == "divide" - divides parent value by the number of children

        Returns
        -------
        resampled: numpy array
            Data array resampled to finer resolution
    """
    data = data_dict["array"]
    refine_ratio = levels_specs[level]["refine_ratio"]
    # the array is resampled (zoomed) with requested interpolation (order = 0 for "nearest")
    # zoom contains one value for each axis
    # mode "nearest" determines how the input array is extended beyond its boundaries
    resampled = scipy.ndimage.zoom(data, zoom=(refine_ratio, refine_ratio), order=0,
                                   mode="nearest", grid_mode=True)
    # if the operation is "repeat", resampled array is the final product
    # if the operation is "divide", then
    # divide the "parent" pixel value by the number of "children" pixels derived from the refine_ratio
    if operation == "divide":
        resampled = resampled.astype(float)
        resampled[resampled == data_dict["nodata"]] = np.nan
        resampled = resampled / refine_ratio ** 2
    return resampled

def resample_masked(data_dict, level, operation, inrasterpath, inmaskpath, categories_dict=None):
    """
    Disaggregate GEMS raster to finer level while applying a mask layer to allocate parent value to children
        Parameters
        ----------
        data_dict: dictionary
            Contains the following keys and values:
                {
                "array": array
                "transform": transform
                "nodata": nodata
                }
            array: numpy array object
                Array from raster
            transform: Affine
                The transform for the raster dataset
            nodata: float or int
                Value to store "absence" of data
        level: int
            Valid GEMS level of the original data, options are: 0, 1, 2, 3, 4, 5, 6
        operation: str
            Defines allocation rule
            operation == "repeat" - repeats parent value to children that meet masking conditions
            operation == "divide" - divides parent value by the number of children that meet masking conditions
            operation == "distribute" - distributes parent value based on proportions from a “suitability” mask
        inrasterpath: str
            Describes the path of the input file
        inmaskpath: str
            Describes the path of the input mask file
        categories_dict: dictionary (required for "divide" and "repeat" operations)
            Describes conditions for masking and weight assigned to each category
            Usage examples:
                {1 : ["(mask == 1)|(mask == 5)", 100]} - only 1 category where pixel value is either 1 or 5
                {1 : ["mask == 1", 60], 2 : ["mask == 5", 20], 3 : ["mask == 6", 20] } - 3 categories with different
                weights (60%, 20%, and 20%)
                {1 : ["(mask > 0) & (mask <= 5 )", 75], 2 : ["mask > 5",25]} - ranges are supported too
        Returns
        -------
        resampled: numpy array
            Data array resampled to finer resolution
     """
    if categories_dict is None:
        categories_dict = {}
    data = data_dict["array"]
    refine_ratio = levels_specs[level]["refine_ratio"]
    # align mask bounds to the bounds of a raster that needs to be disaggregated
    mask, masknodata = align_mask_bounds(inrasterpath, inmaskpath, refine_ratio)
    if operation == "repeat":
        # the array is resampled (zoomed) with requested interpolation (order = 0 for "nearest")
        # zoom contains one value for each axis
        # mode "nearest" determines how the input array is extended beyond its boundaries
        resampled = scipy.ndimage.zoom(data, zoom=(refine_ratio, refine_ratio), order=0,
                                       mode="nearest", grid_mode=True)
        # !!! Note: eval() function introduces potential security vulnerabilities
        resampled[~(eval(categories_dict[1][0]))] = data_dict["nodata"]
    elif operation == "divide":
        resampled = scipy.ndimage.zoom(data, zoom=(refine_ratio, refine_ratio), order=0,
                                       mode="nearest", grid_mode=True)
        resampled = resampled.astype(float)
        resampled[resampled == data_dict["nodata"]] = np.nan
        weighted_matrix = create_weights_matrix(mask, categories_dict, refine_ratio)
        resampled = resampled * weighted_matrix
    elif operation == "distribute":
        data[data == data_dict["nodata"]] = np.nan
        mask = mask.astype(float)
        mask[mask == masknodata] = np.nan
        mask_aggregated = mask.reshape(int(mask.shape[0] / refine_ratio),
                                       refine_ratio,
                                       int(mask.shape[1] / refine_ratio),
                                       refine_ratio).sum(axis=(1, 3))
        ratio = data / mask_aggregated
        ratio_resampled = scipy.ndimage.zoom(ratio, zoom=(refine_ratio, refine_ratio), order=0,
                                             mode="nearest", grid_mode=True)
        resampled = mask * ratio_resampled
    else:
        raise Exception("Operation is not supported; options are: repeat, divide, distribute")
    return resampled
