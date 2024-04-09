'''
PyTest functions for GEMS Grid DGGS utils functions.

© Regents of the University of Minnesota. All rights reserved.
This software is released under an Apache 2.0 license. Further details about the Apache 2.0 license are available in the license.txt file.
'''
import pytest

import numpy as np

from geopandas import GeoDataFrame
from shapely.geometry import Point

from gemsgrid.constants import grid_spec, levels_specs, cell_scale_factors, ease_crs

# from gemsgrid.dggs.utils import _shift_range, shift_range_ease, shift_range_grid_xy, \
#     shift_range_grid_multiple, enumerate_id_elements, gen_point_grid

from gemsgrid.dggs.utils import *

valid_elements = ['00', '01',  '02', '03',
                '10', '11','12', '13',
                '20', '21','22', '23',
                '30', '31','32', '33']

class TestEnumerateIdElements:
    def test_enumerate_id_elements(self,
                                    test = int(4), valid = valid_elements
    ):
        results = enumerate_id_elements(test)
        assert(results ==valid), 'enumerate_id_elements failed to return valid elements'

        results = enumerate_id_elements(4.0)
        assert(not results),' enumerate_id_elments failed to identify wrong input type'

# NOTE: test for enumerate_grid_table_rows were not defined in original library
#   probably need defined at some point
# def test_enumerate_grid_table_rows():

#     results =
#     assert()

test_extent = {'upper_left' : Point(0., 3.),
                'upper_right' : Point(3., 3.),
                'lower_right': Point(3., 0.),
                'lower_left' : Point(0., 0.),
                'delta_x' : 1.0,
                'delta_y' : 1.0}

# x = np.array([0. , 1.5, 3. , 0. , 1.5, 3. , 0. , 1.5, 3. ])
# y= np.array([3. , 3. , 3. , 1.5, 1.5, 1.5, 0. , 0. , 0. ])
x = np.array([0., 1., 2., 3., 0., 1., 2., 3., 0., 1., 2., 3.,0., 1., 2., 3. ])
y = np.array([3., 3., 3., 3., 2., 2., 2., 2., 1., 1., 1., 1., 0., 0., 0., 0. ])

geoms= [Point(x[i], y[i]) for i in range(x.shape[0])]
valid_pt_grid = GeoDataFrame({'ease_x': x, 'ease_y': y, 'geometry' : geoms}, crs=ease_crs)

class TestGenPointGrid:
    def test_gen_point_grid(
        self,
        test = test_extent, valid = valid_pt_grid
    ):

        results = gen_point_grid(
            test['upper_left'], test['upper_right'],
            test['lower_right'], test['lower_left'],
            test['delta_x'], test['delta_y']
        )
        assert(valid.equals(results)), 'gen_point_grid failed to generate valid grid of points'

        results = gen_point_grid(
            test['upper_left'],
            test['upper_right'],
            test['lower_right'],
            test['lower_left'],
            'a',
            'b'
        )
        assert(not results),'gen_point_grid failed to detect invalid type for delta_x/delta_y'

        results = gen_point_grid(
            test['upper_left'].xy,
            test['upper_right'].xy,
            test['lower_right'].xy,
            test['lower_left'].xy,
            test['delta_x'],
            test['delta_y']
        )
        assert(not results), 'gen_point_grid failed to detect invalid type for coordinates'

# NOTE: test for enumerate_grid_table_rows were not defined in original library
#   probably need defined at some point
# def test_calc_grid_coord_vectors():
#     results =
#     assert()

#     results =
#     assert()

shift_tests_dict  = {
    'range_ease' : {
        'x': {
            'test_set' : [
                grid_spec['ease']['min_x'], -levels_specs[0]['x_length'], \
                levels_specs[0]['x_length'], grid_spec['ease']['max_x'],\
                grid_spec['ease']['min_x'] + levels_specs[6]['x_length'],\
                -levels_specs[0]['x_length'] + levels_specs[6]['x_length'],\
                levels_specs[0]['x_length'] - levels_specs[6]['x_length'],\
                grid_spec['ease']['max_x'] - levels_specs[6]['x_length']
            ],
            # 'result_set' : np.array([0.0, 481.0, 483.0,  964.0,\
            #                 2.80e-5, 481.000028, 482.999972, 963.999972]),
            'result_set' : np.array(
                [0.00000000e+00, 4.81000000e+02, 4.83000000e+02, 9.64000000e+02,
                2.77700000e-05, 4.81000028e+02, 4.82999972e+02, 9.63999972e+02]
            ),
        },
        'y' : {
            'test_set' : [
                grid_spec['ease']['max_y'], levels_specs[0]['x_length'],
                -levels_specs[0]['x_length'], grid_spec['ease']['min_y'],
                grid_spec['ease']['max_y'] - levels_specs[6]['x_length'],
                levels_specs[0]['x_length'] - levels_specs[6]['x_length'],
                -levels_specs[0]['x_length'] + levels_specs[6]['x_length'],
                grid_spec['ease']['min_y'] + levels_specs[6]['x_length']
            ],
            # 'result_set': np.array([0.0, 202.0, 204.0, 406.0,
            #                         2.80e-05, 202.000028, 203.999972, 405.999972])
            'result_set': np.array(
                [0.00000000e+00, 2.02000000e+02, 2.04000000e+02, 4.06000000e+02,
                2.77777700e-05, 2.02000028e+02, 2.03999972e+02, 4.05999972e+02]
            )
        },
    },
}

class TestShiftRange:

    # when shifted from ease to gems grid_xy coords, the shifted coords are good to 6 decimal places
    def test_shift_range_ease_x(
        self,
        test = shift_tests_dict['range_ease']['x']['test_set'],
        result = shift_tests_dict['range_ease']['x']['result_set']
    ):
        ''' test_shift_range_ease using x values '''
        comp = np.array([shift_range_ease(x, axis='x') for x in test])
        # print(comp)
        assert(
            (np.around(comp, decimals=6) == np.around(result, decimals=6)).all()
        ), 'shift_range_ease failed to return valid x values'

    def test_shift_range_ease_y(
        self,
        test = shift_tests_dict['range_ease']['y']['test_set'],
        result = shift_tests_dict['range_ease']['y']['result_set']
    ):
        ''' test_shift_range_ease using y values '''
        comp = np.array([shift_range_ease(y, axis='y') for y in test])
        # print(comp)
        assert(
            (np.around(comp, decimals=6) == np.around(result, decimals=6)).all()
        ), 'shift_range_ease failed to return valid y values'

    shift_tests_dict['range_grid_xy'] = {
        'x' : {
            'test_set': [
                0.0,
                (levels_specs[0]['n_col']/2) - 1,
                (levels_specs[0]['n_col']/2) + 1,
                levels_specs[0]['n_col'],
                cell_scale_factors[6],
                (levels_specs[0]['n_col']/2) -1 + cell_scale_factors[6],
                (levels_specs[0]['n_col']/2) + 1 - cell_scale_factors[6],
                levels_specs[0]['n_col'] - cell_scale_factors[6]
            ],
        'result_set': [
            grid_spec['ease']['min_x'],
            -levels_specs[0]['x_length'],
            levels_specs[0]['x_length'],
            grid_spec['ease']['max_x'],
            grid_spec['ease']['min_x'] + levels_specs[6]['x_length'],
            -levels_specs[0]['x_length'] + levels_specs[6]['x_length'],
            levels_specs[0]['x_length'] - levels_specs[6]['x_length'],
            grid_spec['ease']['max_x'] - levels_specs[6]['x_length']
            ]
        },
        'y' : {
            'test_set': [
                0.0,
                (levels_specs[0]['n_row']/2) - 1,
                (levels_specs[0]['n_row']/2) + 1,
                levels_specs[0]['n_row'],
                cell_scale_factors[6],
                (levels_specs[0]['n_row']/2) -1 + cell_scale_factors[6],
                (levels_specs[0]['n_row']/2) + 1 - cell_scale_factors[6],
                levels_specs[0]['n_row'] - cell_scale_factors[6]
            ],
            'result_set': [
                grid_spec['ease']['max_y'],
                levels_specs[0]['x_length'],
                -levels_specs[0]['x_length'],
                grid_spec['ease']['min_y'],
                grid_spec['ease']['max_y'] - levels_specs[6]['x_length'],
                levels_specs[0]['x_length'] - levels_specs[6]['x_length'],
                -levels_specs[0]['x_length'] + levels_specs[6]['x_length'],
                grid_spec['ease']['min_y'] + levels_specs[6]['x_length']
            ]
        }
    }

    # when shifted from gems grid_xy coords, the resulting ease coords are good to 5 decimal places
    def test_shift_range_grid_xy_x(
        self,
        test = shift_tests_dict['range_grid_xy']['x']['test_set'],
        result = shift_tests_dict['range_grid_xy']['x']['result_set']
    ):
        '''test_shift_range_grid_xy using x values '''
        comp = np.array([shift_range_grid_xy(x, axis='x') for x in test])
        # print(comp)
        assert(
            (np.around(comp, decimals=5) == np.around(result, decimals = 5)).all()
        ), 'shift_range_grid_xy failed to return valid x values'

    def test_shift_range_grid_xy_y(
        self,
        test = shift_tests_dict['range_grid_xy']['y']['test_set'],
        result = shift_tests_dict['range_grid_xy']['y']['result_set']
    ):
        '''test test_shift_range_grid using y values '''
        comp = np.array([shift_range_grid_xy(y, axis='y') for y in test])
        # print(comp)
        assert(
            (np.around(comp, decimals=5) == np.around(result, decimals=5)).all()
        ), 'shift_range_grid_xy failed to return valid y values'

    grid_len = levels_specs[0]['x_length']
    shift_tests_dict['range_grid_multiple'] = {
        'x' : {
            'test_set': [
                0.0,
                ((levels_specs[0]['n_col']/2) - 1) * grid_len,
                ((levels_specs[0]['n_col']/2) + 1) * grid_len,
                levels_specs[0]['n_col'] * grid_len,
                    # test some level 1 distances
                (3 * cell_scale_factors[1]) * grid_len,
                ((levels_specs[0]['n_col']/2) -1 + 2 * cell_scale_factors[1]) * grid_len,
                ((levels_specs[0]['n_col']/2) + 1 - 2 * cell_scale_factors[1]) * grid_len,
                (levels_specs[0]['n_col'] -   cell_scale_factors[1]) * grid_len,
            ],
            'result_set': [
                grid_spec['ease']['min_x'],
                -levels_specs[0]['x_length'],
                levels_specs[0]['x_length'],
                grid_spec['ease']['max_x'],
                # corresponding L1 results
                grid_spec['ease']['min_x'] + 3 * levels_specs[1]['x_length'],
                -levels_specs[0]['x_length'] + 2 * levels_specs[1]['x_length'],
                levels_specs[0]['x_length'] - 2 * levels_specs[1]['x_length'],
                grid_spec['ease']['max_x'] -  levels_specs[1]['x_length'],
            ]
        },
        'y' : {
            'test_set': [
                0.0,
                ((levels_specs[0]['n_row']/2) - 1) * grid_len,
                ((levels_specs[0]['n_row']/2) + 1) * grid_len,
                (levels_specs[0]['n_row']) * grid_len,
                (2 * cell_scale_factors[1]) * grid_len,
                ((levels_specs[0]['n_row']/2) -1 + cell_scale_factors[1]) * grid_len,
                ((levels_specs[0]['n_row']/2) + 1 - 2 *  cell_scale_factors[1]) * grid_len,
                (levels_specs[0]['n_row'] - cell_scale_factors[1]) * grid_len,
            ],
            'result_set': [
                grid_spec['ease']['max_y'],
                levels_specs[0]['x_length'],
                -levels_specs[0]['x_length'],
                grid_spec['ease']['min_y'],
                (grid_spec['ease']['max_y'] - 2 * levels_specs[1]['x_length']),
                (levels_specs[0]['x_length'] - 1* levels_specs[1]['x_length']),
                (-levels_specs[0]['x_length'] + 2 * levels_specs[1]['x_length']),
                (grid_spec['ease']['min_y'] +  levels_specs[1]['x_length']),
            ]
        }
    }

    def test_shift_range_grid_multiple_x(
            self,
            test = shift_tests_dict['range_grid_multiple']['x']['test_set'],
            result = shift_tests_dict['range_grid_multiple']['x']['result_set']
        ):
        '''test_shift_range_grid_multiple_x using x values '''
        comp = np.array([shift_range_grid_multiple(x, axis='x') for x in test])
        # print(comp)
        assert((np.around(comp, decimals=5) == np.around(result, decimals = 5)).all()), \
            'test_shift_range_grid_multiple_x failed to return valid x values'

    def test_shift_range_grid_multiple_y(
        self,
        test = shift_tests_dict['range_grid_multiple']['y']['test_set'],
        result = shift_tests_dict['range_grid_multiple']['y']['result_set']
    ):
        '''test_shift_range_grid_multiple_y using y values '''
        comp = np.array([shift_range_grid_multiple(y, axis='y') for y in test])
        # print(comp)
        assert(
            (np.around(comp, decimals=5) == np.around(result, decimals=5)).all()
        ), 'test_shift_range_grid_multiple_y failed to return valid y values'

test = ['ul', 'ur', 'lr', 'll']
res = {'forward' : [('ul', 'ur'), ('ur', 'lr'), ('lr', 'll'), ('ll', 'ul')],
        'reverse' : [('ll', 'lr'), ('lr', 'ur'), ('ur', 'ul'), ('ul', 'll')]}
class TestPairwiseCircle:
    def test_pairwise_circle_forward(
        self,
        test = test,
        result = res
    ):
        comp = list(pairwise_circle(test))
        assert(comp == result['forward']), 'pairwise_circle failed to return expected results in the forward direction'

    def test_pairwise_circle_reverse(
        self,
        test = test,
        result = res
    ):
        comp = list(pairwise_circle(test, reverse = True))
        assert(comp == result['reverse']), 'pairwise_circle failed to return expected results in the reverse direction'

test = [['a', 'b', 'c'], ['d', 'e'], ['f']]
res = ['a', 'b', 'c', 'd', 'e', 'f']
class TestFlatten:
    def test_flatten(
        self,
        test = test,
        res = res
    ):
        comp = flatten(test)
        assert(comp == res), 'Flatten failed to return expected results'

test = [1.00005, 1.000055]
res = True
class TestEpsilonCheck:
    def test_epsilon_check(
            self,
            test = test,
            result = res
        ):
        comp = epsilon_check(test[0], test[1])
        assert(comp == result),'epsilon_check failed to valid value'

test = np.array([1.123456789, 426.123456789])
res = np.array([1.12345, 426.12345])
class TestTrunc:
    def test_trunc(
        self,
        test = test,
        result = res
    ):
        comp = trunc(test, decimals = 5)
        assert(comp == result).all(), 'trunc failed to return expected results.'
