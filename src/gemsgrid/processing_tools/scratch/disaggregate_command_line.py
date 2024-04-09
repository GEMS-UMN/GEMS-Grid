'''
Module supports disggreation on the command line.

© Regents of the University of Minnesota. All rights reserved.
This software is released under an Apache 2.0 license. Further details about the Apache 2.0 license are available in the license.txt file.
'''
import gemsgrid.disaggregate_vectors_restructured as dv
import gemsgrid.disaggregate_rasters_restructured as dr
import argparse
import ast
import pyproj

pyproj.network.set_network_enabled(active=True)

# an attempt to combine 4 disaggregate functions into 1 function
# and implement argparse

def disaggregate (**kwards):
    """
    Disaggregate raster or vector data to GEMS
    """
    if kwards["operation"] not in ["repeat", "divide"]:
        raise Exception("Operation is not supported; options are: repeat, divide")

    print ("STEP 1 of 4: Open input file")
    if kwards["subcommand"] == "vector_masked" or kwards["subcommand"] == "vector_unmasked":
        ease_gdf = dv.open_and_project_vector(kwards["invectorpath"])
    elif kwards["subcommand"] == "raster_masked" or kwards["subcommand"] == "raster_unmasked":
        data_dict = dr.open_raster(kwards["inrasterpath"])

    print("STEP 2 of 4: Generate geoproperties")
    if kwards["subcommand"] == "vector_unmasked":
        dict_geoproperties = dv.generate_raster_geoproperties(ease_gdf, kwards["target_level"], kwards["globalextent"])
    elif kwards["subcommand"] == "vector_masked":
        dict_geoproperties = dv.generate_raster_geoproperties_and_maskarray(ease_gdf, kwards["inmaskpath"], kwards["clip"])
    elif kwards["subcommand"] == "raster_masked" or kwards["subcommand"] == "raster_unmasked":
        scaled_transform = dr.scale_transform(data_dict["transform"], kwards["source_level"])

    print("STEP 3 of 4: Produce disaggregated array")
    if kwards["subcommand"] == "vector_unmasked":
        rasterized = dv.rasterize_unmasked(ease_gdf, kwards["var"], kwards["operation"], dict_geoproperties)
    elif kwards["subcommand"] == "vector_masked":
        rasterized = dv.rasterize_masked(ease_gdf, kwards["var"], kwards["operation"], dict_geoproperties, kwards["categories_dict"])
    elif kwards["subcommand"] == "raster_unmasked":
        resampled = dr.resample_unmasked(data_dict, kwards["source_level"], kwards["operation"])
    elif kwards["subcommand"] == "raster_masked":
        resampled = dr.resample_masked(data_dict, kwards["source_level"], kwards["operation"], kwards["inrasterpath"], kwards["inmaskpath"], kwards["categories_dict"])

    print("STEP 4 of 4: Save disaggregated array to raster")
    if kwards["subcommand"] == "vector_masked" or kwards["subcommand"] == "vector_unmasked":
        dv.save_raster(kwards["outrasterpath"], rasterized, dict_geoproperties["dst_transform"])
    elif kwards["subcommand"] == "raster_masked" or kwards["subcommand"] == "raster_unmasked":
        dr.save_raster(kwards["outrasterpath"], resampled, scaled_transform, data_dict["nodata"])

parser = argparse.ArgumentParser(description="Disaggregation tool")

# only the following 2 arguments are ALWAYS required
parser.add_argument("-or",
                    "--outrasterpath",
                    metavar='',
                    required=True,
                    help="Describes the path of the output raster file")
parser.add_argument("-o",
                    "--operation",
                    metavar='',
                    required=True,
                    help="Defines allocation rule")

# SUBPARSERS
subparsers = parser.add_subparsers(dest="subcommand", title="subcommand")

# VECTOR UNMASKED
parser_vector_unmasked = subparsers.add_parser("vector_unmasked", help="Input data is vector, mask is not available")
parser_vector_unmasked.add_argument("-iv",
                                    "--invectorpath",
                                    metavar='',
                                    help="Describes the path of the input vector data")
parser_vector_unmasked.add_argument("-v",
                                    "--var",
                                    metavar='',
                                    help="Column name from the attribute table that needs to be disaggregated")
parser_vector_unmasked.add_argument("-tl",
                                    "--target_level",
                                    type=int,
                                    metavar='',
                                    help="Valid GEMS level, options are: 0, 1, 2, 3, 4, 5, 6")
parser_vector_unmasked.add_argument("-g",
                                    "--globalextent",
                                    metavar='',
                                    help="Specifies if vector data are global "
                                         "(globalextnet=True, otherwise globalextnet=False)")
# VECTOR MASKED
parser_vector_masked = subparsers.add_parser("vector_masked", help="Input data is vector, mask is available")
parser_vector_masked.add_argument("-iv",
                                  "--invectorpath",
                                  metavar='',
                                  help="Describes the path of the input vector data")
parser_vector_masked.add_argument("-v",
                                  "--var",
                                  metavar='',
                                  help="Column name from the attribute table that needs to be disaggregated")
parser_vector_masked.add_argument("-im",
                                  "--inmaskpath",
                                  metavar='',
                                  help="Describes the path of the input mask file")
parser_vector_masked.add_argument("-cd",
                                  "--categories_dict",
                                  metavar='',
                                  help="Describes conditions for masking and weight assigned to each category")
parser_vector_masked.add_argument("-c",
                                  "--clip",
                                  metavar='',
                                  help="Specifies if mask raster has substantially larger extent compared to the input vector data"
                                       "and needs to be clipped (clip=True, otherwise clip=False)")

# RASTER UNMASKED
parser_raster_unmasked = subparsers.add_parser("raster_unmasked", help="Input data is raster, mask is not available")
parser_raster_unmasked.add_argument("-ir",
                                    "--inrasterpath",
                                    metavar='',
                                    help="Describes the path of the input file")
parser_raster_unmasked.add_argument("-sl",
                                    "--source_level",
                                    type=int,
                                    metavar='',
                                    help="Valid GEMS level of the original data, options are: 0, 1, 2, 3, 4, 5, 6")

# RASTER MASKED
parser_raster_masked = subparsers.add_parser("raster_masked", help="Input data is raster, mask is available")
parser_raster_masked.add_argument("-ir",
                                  "--inrasterpath",
                                  metavar='',
                                  help="Describes the path of the input file")
parser_raster_masked.add_argument("-sl",
                                  "--source_level",
                                  type=int,
                                  metavar='',
                                  help="Valid GEMS level of the original data, options are: 0, 1, 2, 3, 4, 5, 6")
parser_raster_masked.add_argument("-im",
                                  "--inmaskpath",
                                  metavar='',
                                  help="Describes the path of the input mask file")
parser_raster_masked.add_argument("-cd",
                                  "--categories_dict",
                                  metavar='',
                                  help="Describes conditions for masking and weight assigned to each category")

args = parser.parse_args()
print (args)


if args.subcommand == "vector_unmasked":
    print ("Input data is vector, mask is not available")
    params = {
        "subcommand" : args.subcommand,
        "outrasterpath": args.outrasterpath,
        "operation": args.operation,
        "invectorpath" : args.invectorpath,
        "var" : args.var,
        "target_level" : args.target_level,
        "globalextent" : eval(args.globalextent)
    }
elif args.subcommand == "vector_masked":
    print("Input data is vector, mask is available")
    params = {
        "subcommand": args.subcommand,
        "outrasterpath": args.outrasterpath,
        "operation": args.operation,
        "invectorpath" : args.invectorpath,
        "var" : args.var,
        "inmaskpath" : args.inmaskpath,
        "categories_dict" : ast.literal_eval(args.categories_dict),
        "clip" : eval(args.clip)
    }
elif args.subcommand == "raster_unmasked":
    print("Input data is raster, mask is not available")
    params = {
        "subcommand": args.subcommand,
        "outrasterpath": args.outrasterpath,
        "operation": args.operation,
        "inrasterpath": args.inrasterpath,
        "source_level": args.source_level
    }
elif args.subcommand == "raster_masked":
    print("Input data is raster, mask is not available")
    params = {
        "subcommand": args.subcommand,
        "outrasterpath": args.outrasterpath,
        "operation": args.operation,
        "inrasterpath": args.inrasterpath,
        "source_level": args.source_level,
        "inmaskpath": args.inmaskpath,
        "categories_dict": ast.literal_eval(args.categories_dict)
    }
else:
    print("This subcommand does not exist, choose one of the following: "
          "vector_unmasked, vector_masked, raster_umasked, raster_masked")
    params = {}

print (params)
disaggregate(**params)
