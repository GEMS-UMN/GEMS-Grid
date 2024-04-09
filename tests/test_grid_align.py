'''
Module for testing GEMS Grid geotransforms.

© Regents of the University of Minnesota. All rights reserved.
This software is released under an Apache 2.0 license. Further details about the Apache 2.0 license are available in the license.txt file.
'''
import numpy as np

from gemsgrid.constants import levels_specs, ease_crs, geo_crs
from gemsgrid.dggs.utils import epsilon_check, pairwise_circle
from gemsgrid.grid_align import e2w, gems_grid_bounds, grid_id_to_corner_coord, gems_align_check

class TestGridIdToCornerCoords:
    test_set = ['L6.202481.00.00.00.00.00.00', 'L6.202483.00.00.00.00.00.00',
                'L6.204483.00.00.00.00.00.00', 'L6.204481.00.00.00.00.00.00']
    # result_set = np.array([[-36032.22084,  36032.22084], [ 36032.22084,  36032.22084],
    #                         [ 36032.22084, -36032.22084], [-36032.22084, -36032.22084]])
    result_set = np.array([(17331498.22432, 7278508.6098),
                        (17403562.66600, 7278508.6098),
                        (17403562.66600, 7350573.05148),
                        (17331498.22432, 7350573.05148)])

    def test_grid_id_to_corner_coords(
        self,
        test=test_set,
        result=result_set
    ):
        comp = [grid_id_to_corner_coord(t, level=6) for t in test]
        # comp = np.around(np.array(comp),
        assert ((np.around(comp, decimals=5) == result).all()), \
            'Grid XY to corner failed to return correct values'
        # print(comp)

######################
#
# gems_grid_bounds tests
#
######################
# going to use a couple of functions here.
#   the aim is to allow for testing of more cases, hopefully
#   making the results more robust
def gen_dim_test(
    start,
    stop,
    interval,
    dim,
    edge=levels_specs[0]['x_length'],
    offset=0
):
    """This will generate a series of bounds that can be used to test gems_grid_bounds.
        Basically, creates a 'base bound' that is ~ 2 x 2 Level 0 grid cells, that are modified
        by some 'offset'. The 'base bound' is then shifted one Level 0 grid cell across either:
            + x axis of EASE v2 grid
            - y axis of EASE v2 grid

        This is functional, not elegant.
    """
    corners = []
    bounds = []
    for i in range(start, stop, interval):

        if dim == 'x':
            ul_x = ll_x = (i - 1) * edge + offset
            ul_y = ur_y = edge - offset

            ur_x = lr_x = (i + 1) * edge - offset
            lr_y = ll_y = -edge + offset

        elif dim == 'y':
            ul_x = ll_x = -edge + offset
            ul_y = ur_y = (i + 1) * edge - offset

            ur_x = lr_x = edge - offset
            lr_y = ll_y = (i - 1) * edge + offset
        else:
            break

        ease_corners = np.array([[ul_x, ul_y], [ur_x, ur_y], [lr_x, lr_y], [ll_x, ll_y]])
        corners.append([[ul_x, ul_y], [ur_x, ur_y], [lr_x, lr_y], [ll_x, ll_y]])
        bounds.append([(ease_corners[:, 0].min()), ease_corners[:, 1].min(),
                    ease_corners[:, 0].max(), ease_corners[:, 1].max()])

    return np.array(corners), np.array(bounds)

def gen_results(
    wgs_corners,
    level,
    source_crs
):
    """This function will take wgs_corners and run the tests.
        This will make it easy to run each of the test cases generated using
        gen_dim_test to run, meaning we can then do just a single test of the
        whole set at the end.

        Similarly, this is also functional, not at all elegant.
    """
    res = []
    for i in range(wgs_corners.shape[0]):
        min_x = wgs_corners[i][:, 0].min()
        min_y = wgs_corners[i][:, 1].min()
        max_x = wgs_corners[i][:, 0].max()
        max_y = wgs_corners[i][:, 1].max()

        res.append(np.array(gems_grid_bounds(bounds=(min_x, min_y, max_x, max_y),
                                            level=level, source_crs=source_crs)))

    return np.array(res)

def to_wgs_corners(
    corners
):
    """A second part of these test will be to convert bounds in EASE to lon,lat.
        This function does that conversion

        This is also functional, not elegant
    """
    wgs_corners = []

    for vertices in corners:
        nc = [e2w(vertices[i][0], vertices[i][1]) for i in range(len(vertices))]
        wgs_corners.append(nc)

    return np.array(wgs_corners)

class TestGemsGridBoundsEase:
    def test_gems_grid_bounds_ease_xdim(self):
        corners, bounds = \
            gen_dim_test(
                start=0,
                stop=int(levels_specs[0]['n_col'] / 2),
                interval=1,
                dim='x')
        test = gen_results(corners, level=0, source_crs=ease_crs)
        assert (epsilon_check(test, bounds).all()), \
            'x-dim test of gems_grid_bounds using L0 EASE coords failed.'

        return bounds

    def test_gems_grid_bounds_ease_ydim(self):
        corners, bounds = \
            gen_dim_test(
                start=0,
                stop=-int(levels_specs[0]['n_row'] / 2),
                interval=-1,
                dim='y')
        test = gen_results(corners, level=0, source_crs=ease_crs)
        comp = epsilon_check(test, bounds).all()
        assert (comp), 'y-dim test of gems_grid_bounds using L0 EASE coords failed.'

    def test_gems_grid_bounds_geo_xdim(self):
        corners, bounds = \
            gen_dim_test(
                start=0,
                stop=int(levels_specs[0]['n_col'] / 2),
                interval=1,
                dim='x')
        corners = to_wgs_corners(corners)
        test = gen_results(corners, level=0, source_crs=geo_crs)
        # comp = epsilon_check(test, bounds).all()
        assert (epsilon_check(test, bounds).all()), \
            'x-dim test of gems_grid_bounds using L0 Geo coords failed.'

        return bounds

    def test_gems_grid_bounds_geo_ydim(self):
        corners, bounds = \
            gen_dim_test(
                start=0,
                stop=-int(levels_specs[0]['n_row'] / 2),
                interval=-1,
                dim='y')
        corners = to_wgs_corners(corners)
        test = gen_results(corners, level=0, source_crs=geo_crs)
        comp = epsilon_check(test, bounds).all()
        assert (comp), 'y-dim test of gems_grid_bounds using L0 Geo coords failed.'

######
#
# next, repeat the tests, but removing the equiv of one L6 cell from each bounds
#   when testing with target of L0, the results should match bounds generated above
#   when testing with target of L6, they should match bounds generated below
#
######
    _, L0_x_bounds = gen_dim_test(start=0, stop=int(levels_specs[0]['n_col'] / 2), interval=1,
                                dim='x')
    _, L0_y_bounds = gen_dim_test(start=0, stop=-int(levels_specs[0]['n_row'] / 2), interval=-1,
                                dim='y')

    def test_gems_grid_bounds_geo_l6(
        self,
        results=L0_x_bounds
    ):
        corners, bounds = \
            gen_dim_test(
                start=0,
                stop=int(levels_specs[0]['n_col'] / 2),
                interval=1,
                dim='x',
                offset=levels_specs[6]['x_length'])
        corners = to_wgs_corners(corners)
        test = gen_results(corners, level=0, source_crs=geo_crs)
        assert (epsilon_check(test, results).all()), \
            'x-dim test of gems_grid_bounds using L6 Geo coords to L0 GEMS grid failed.'

        test = gen_results(corners, level=6, source_crs=geo_crs)
        assert (epsilon_check(test, bounds).all()), \
            'x-dim test of gems_grid_bounds using L6 Geo coords to L6 GEMS grid failed.'

    def test_gems_grid_bounds_geo_l6_to_l0_xdim(
        self,
        results=L0_y_bounds
    ):
        corners, bounds = \
            gen_dim_test(
                start=0,
                stop=-int(levels_specs[0]['n_row'] / 2),
                interval=-1,
                dim='y')
        corners = to_wgs_corners(corners)
        test = gen_results(corners, level=0, source_crs=geo_crs)
        assert (epsilon_check(test, results).all()), \
            'x-dim test of gems_grid_bounds using L6 Geo coords to L0 GEMS grid failed.'

        test = gen_results(corners, level=6, source_crs=geo_crs)
        assert (epsilon_check(test, bounds).all()), \
            'x-dim test of gems_grid_bounds using L6 Geo coords to L6 GEMS grid failed.'

class TestGemsAlignCheck:
    def test_gems_align_check_aligned(self):
        aligned_reference = {
            'Projection is EASE-Grid 2.0 (EPSG:6933):': 'Pass',
            'Dataset is rectilinear:': 'Pass',
            'X and Y size are equal:': 'Pass',
            'Cell size matches a GEMS grid resolution:': 'Pass',
            'The X dimension of the cell corners matches a GEMS grid corner:': 'Pass',
            'The Y dimension of the cell corners matches a GEMS grid corner:': 'Pass',
            'Tests passed out of 6:': '6'
        }
        aligned_results = gems_align_check('tests/data/aligned_l1_unprojected_wgs84.tif', 1)

        assert (aligned_reference == aligned_results), \
            'Unexpected alignment test results for tests/data/aligned_l1_unprojected_wgs84.tif'

    def test_gems_align_check_unaligned(self):
        unaligned_reference = {
            'Projection is EASE-Grid 2.0 (EPSG:6933):': 'Fail. Supplied CRS is EPSG:4326',
            'Dataset is rectilinear:': 'Pass',
            'X and Y size are equal:': 'Fail',
            'Cell size matches a GEMS grid resolution:': 'Fail',
            'The X dimension of the cell corners matches a GEMS grid corner:': 'Fail. Difference = 0.01445',
            'The Y dimension of the cell corners matches a GEMS grid corner:': 'Fail. Difference = 0.03537',
            'Tests passed out of 6:': '1'
        }
        unaligned_results = gems_align_check('tests/data/unprojected_wgs84.tif', 1)

        assert (unaligned_reference == unaligned_results), \
            'Unexpected alignment test results for tests/data/unprojected_wgs84.tif'
