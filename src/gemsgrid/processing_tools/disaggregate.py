'''
This module accomplishes the disaggregation.

© Regents of the University of Minnesota. All rights reserved.
This software is released under an Apache 2.0 license. Further details about the Apache 2.0 license are available in the license.txt file.
'''
import gemsgrid.processing_tools.disaggregate_vectors as dv
import gemsgrid.processing_tools.disaggregate_rasters as dr
from gemsgrid.dggs.checks import check_level
from gemsgrid.logConfig import logger

def disaggregate (**kwards):
    """
    Disaggregate raster or vector data to GEMS
        Parameters
        ----------
        input_type: str
            Describes the type of input data ("vector_unmasked", "vector_masked", "raster_unmasked", "raster_masked")
        outrasterpath: str
            Describes the path of the output raster file
        operation: str
            Defines allocation rule
            operation == "repeat" - repeats parent value to children
            operation == "divide" - divides parent value by the number of children
            operation == "distribute" - distributes parent value based on proportions from a “suitability” mask
        invectorpath: str
            Describes the path of the input shapefile
        var: str
            Column name from the attribute table that needs to be disaggregated
        target_level: int
            Valid GEMS level, options are: 0, 1, 2, 3, 4, 5, 6
        globalextent: boolean
            Specifies if vector data are global (globalextnet=True, otherwise globalextnet=False)
        inmaskpath: str
            Describes the path of the input mask file
        vectornodata: float or int (optional)
            Value to store "absence" of data; defaults to -9999
        categories_dict: dictionary (required for "divide" and "repeat" operations)
            Describes conditions for masking and weight assigned to each category
            Note: is using operation = "repeat" only 1 category  with weight 100%  can be specified
            (even if it includes multiple classes)
            Usage examples:
                {1: ["(mask == 1) | (mask == 5)", 100]}
                {1: ["mask == 1", 100]}
            One or multiple categories with different weights can be provided for operation "divide":
            Usage examples:
                {1: ["(mask == 1) | (mask == 5)", 100]} - only 1 category where pixel value is either 1 or 5
                {1: ["mask == 1", 60], 2 : ["mask == 5", 20], 3 : ["mask == 6", 20] } - 3 categories with different
                weights (60%, 20%, and 20%)
                {1: ["(mask > 0) & (mask <= 5)", 75], 2 : ["mask > 5", 25]} - two categories defined by a range of
                values
        clip: boolean
            Specifies if mask raster has substantially larger extent compared to the input vector data
            and needs to be clipped (clip=True, otherwise clip=False)
        inrasterpath: str
            Describes the path of the input raster file
        source_level: int
            Valid GEMS level of the original data, options are: 0, 1, 2, 3, 4, 5, 6
        Returns
        -------
        no return
        (saves the disaggregated output file to outrasterpath defined above)
    """
    if kwards["input_type"] not in ["vector_unmasked", "vector_masked", "raster_unmasked", "raster_masked"]:
        raise Exception("Input type does not exist; options are: vector_unmasked, vector_masked, raster_unmasked, "
                        "raster_masked")
    if "operation" in kwards and kwards["operation"] not in ["repeat", "divide", "distribute"]:
        raise Exception("Operation is not supported; options are: repeat, divide, distribute")
    if "source_level" in kwards and not check_level(kwards["source_level"]):
        raise Exception("Invalid grid level; options are: 0, 1, 2, 3, 4, 5, 6")
    if "target_level" in kwards and not check_level(kwards["target_level"]):
        raise Exception("Invalid grid level; options are: 0, 1, 2, 3, 4, 5, 6")

    if kwards["input_type"] == "vector_unmasked":
        logger.debug("STEP 1 of 4: Open input file")
        ease_gdf = dv.open_and_project_vector(kwards["invectorpath"])
        logger.debug("STEP 2 of 4: Generate geoproperties")
        dict_geoproperties = dv.generate_raster_geoproperties(ease_gdf, kwards["target_level"], kwards["globalextent"])
        logger.debug("STEP 3 of 4: Produce disaggregated array")
        rasterized = dv.rasterize_unmasked(ease_gdf, kwards["var"], dict_geoproperties, kwards["operation"],
                                           kwards.get("vectornodata", -9999))
        logger.debug("STEP 4 of 4: Save disaggregated array to raster")
        dv.save_raster(kwards["outrasterpath"], rasterized, dict_geoproperties["dst_transform"],
                       kwards.get("vectornodata", -9999))
    elif kwards["input_type"] == "vector_masked":
        logger.debug("STEP 1 of 4: Open input file")
        ease_gdf = dv.open_and_project_vector(kwards["invectorpath"])
        logger.debug("STEP 2 of 4: Generate geoproperties")
        dict_geoproperties = dv.generate_raster_geoproperties_and_maskarray(ease_gdf, kwards["inmaskpath"],
                                                                            kwards["clip"])
        logger.debug("STEP 3 of 4: Produce disaggregated array")
        rasterized = dv.rasterize_masked(ease_gdf, kwards["var"], dict_geoproperties, kwards["operation"],
                                         kwards.get("vectornodata", -9999), kwards.get("categories_dict", None))
        logger.debug("STEP 4 of 4: Save disaggregated array to raster")
        dv.save_raster(kwards["outrasterpath"], rasterized, dict_geoproperties["dst_transform"],
                       kwards.get("vectornodata", -9999))
    elif kwards["input_type"] == "raster_unmasked":
        logger.debug("STEP 1 of 4: Open input file")
        data_dict = dr.open_raster(kwards["inrasterpath"])
        logger.debug("STEP 2 of 4: Generate geoproperties")
        scaled_transform = dr.scale_transform(data_dict["transform"], kwards["source_level"])
        logger.debug("STEP 3 of 4: Produce disaggregated array")
        resampled = dr.resample_unmasked(data_dict, kwards["source_level"], kwards["operation"])
        logger.debug("STEP 4 of 4: Save disaggregated array to raster")
        dr.save_raster(kwards["outrasterpath"], resampled, scaled_transform, data_dict["nodata"])
    elif kwards["input_type"] == "raster_masked":
        logger.debug("STEP 1 of 4: Open input file")
        data_dict = dr.open_raster(kwards["inrasterpath"])
        logger.debug("STEP 2 of 4: Generate geoproperties")
        scaled_transform = dr.scale_transform(data_dict["transform"], kwards["source_level"])
        logger.debug("STEP 3 of 4: Produce disaggregated array")
        resampled = dr.resample_masked(data_dict, kwards["source_level"], kwards["operation"], kwards["inrasterpath"],
                                       kwards["inmaskpath"], kwards.get("categories_dict", None))
        logger.debug("STEP 4 of 4: Save disaggregated array to raster")
        dr.save_raster(kwards["outrasterpath"], resampled, scaled_transform, data_dict["nodata"])
