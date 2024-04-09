'''
Unit tests for GEMS Grid constants.py module.

© Regents of the University of Minnesota. All rights reserved.
This software is released under an Apache 2.0 license. Further details about the Apache 2.0 license are available in the license.txt file.
'''
import pytest

import numpy as np
from pyproj import Transformer

from gemsgrid.constants import levels_specs, grid_spec

# consensus was to generate the grid and level specifications
#   using code. the functions to do this are here
def _define_grid_levels_specs():
    '''Calculate and define the specifications for the GEMS Grid.

    Parameters
    ----------
    geo_crs : int
        EPSG code for geographic coordinate reference system
    ease_crs : _type_
        _description_

    Returns
    -------
    grid_spec : dictonary
        Dictonary containing GEMS Grid parameters/specifications.
    levels_specs : dictonary
        Dictonary containing level specification for GEMS Grid
    ease_crs : int
        EPSG Code value for EASE v2
    geo_crs : int
        EPSG Code value for geographic coordinates
    cell_scale_factors : np.array
        Scaling factors used internally by GEMS Grid library
    mult_fact : list
        Multiplication factors; used by DHP
    e2w : pyproj Transformer object
        Convenince function for transforming EASE v2 to WGS84 coordinates
    w2e : pyproj Transformer object
        Convenince function for transforming WGS84 to EASE v2 coordinates
    '''
    ease_crs = 6933
    geo_crs = 4326

    # define the pyproj Transforms necessary. need both a
    #   from WGS84 -> EASE v2 (w2e) and
    #   from EASE v2 -> WGS84 (e2w)
    w2e = Transformer.from_crs(geo_crs, ease_crs, always_xy=True).transform
    e2w = Transformer.from_crs(ease_crs, geo_crs, always_xy=True).transform

    lon = -180.0
    lat = 0.0
    n_row = 406
    n_col = 964

    # David used the mult_fac in composing his grid specs
    #   it is conventient, and similar to how Jeff achieved
    #   similar but using their inverse as a scale factor
    #       e.g. cell_scale_factors
    # both are defined here, and then exported for
    mult_fac = [ 1, 4, 12, 36, 360, 3600, 36000 ]
    # level '6' has no refinement ratio, by design.
    #    can be extended to finer resolution, as required
    #    e.g.
    refine_ratio = [4, 3, 3, 10, 10, 10, 10]
    # refine_ratio = [4, 3, 3, 10, 10, 10, None]

    cell_scale_factors = np.array([1.0 / mf for mf in mult_fac])

    # calculate the max_x for ease
    ease_ul_x, _ = w2e(lon, lat)
    # print(ease_ul_x)
    ease_ul_y = ease_ul_x * n_row / n_col
    # ease_ur_x = -ease_ul_x

    _, geo_ul_y = e2w(ease_ul_x, ease_ul_y)
    # geo_ul_y = -geo_ul_y

    # using the coordinates determined above, we can specific the
    #   extent/bounding box in both EASE and Geographic coords
    valid_grid_spec = {'ease' : {
                      'min_x' : ease_ul_x,
                      'min_y' : ease_ul_y,
                      'max_x' : -ease_ul_x,
                      'max_y' : -ease_ul_y
                        },
                  'geo' : {
                      'min_x' : lon,
                      'min_y' : geo_ul_y,
                      'max_x' : -lon,
                      'max_y' : -geo_ul_y
                        }
                }
    # define levels_specs programatically. likely some unneed reduncancy here
    valid_levels_specs ={}
    for i in range(7):
        valid_levels_specs[int(i)] = {'refine_ratio': refine_ratio[i],
                                'n_row' : n_row * mult_fac[i],
                                'n_col' : n_col * mult_fac[i],
                                'x_length' : 2 * valid_grid_spec['ease']['max_x'] / (n_col * mult_fac[i]),
                                'y_length' : 2 * valid_grid_spec['ease']['max_y'] / (n_row *  mult_fac[i])
                                }

    return (valid_grid_spec, valid_levels_specs, # grid, levels spects
            cell_scale_factors, mult_fac, # scaling factors
        )

valid_grid_spec, valid_levels_specs, \
valid_cell_scale_factors, \
valid_mult_fac = _define_grid_levels_specs()
sf = 13
class TestDefineGridSpec:

    def test_define_grid_specs(
        self,
        test =  grid_spec,
        valid = valid_grid_spec,
        sf= sf
    ):
        # test the grid spec first
        comp = [np.allclose(test[key1][key2], valid[key1][key2], atol =sf) \
            for key1 in test.keys() for key2 in test[key1].keys()]

        assert (all(comp)), 'Grid specification not accurate to {} decimal places'.format(sf)

class TestDefineLevelsSpecs:
    def test_define_levels_specs(
        self,
        test = levels_specs,
        valid = valid_levels_specs,
        sf= sf
    ):
        print(valid_levels_specs)

        comp = [np.allclose(test[key1][key2], valid[key1][key2], atol= sf) \
            for key1 in test.keys() for key2 in test[key1].keys()]

        assert (all(comp)), 'Levels specifications not accurate to {} decimal places'.format(sf)
