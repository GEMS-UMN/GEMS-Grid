'''
Unit tests for GEMS Grid DGGS valdiate.py functions.

© Regents of the University of Minnesota. All rights reserved.
This software is released under an Apache 2.0 license. Further details about the Apache 2.0 license are available in the license.txt file.
'''
import pytest

import numpy as np

from gemsgrid.constants import levels_specs
from tests.conftest import TestDict

# from gemsgrid.dggs.validate import check_coord_range, check_coords_range, \
#     validate_ccd sroords_lon_lat, check_level, check_gid_format, check_grid_ids_format, \
#     check_gid_l0_index, check_grid_ids_l0_index, check_gid_num_element, \
#     check_gid_start_with, check_grid_ids_starts_with, validate_grid_ids
from gemsgrid.dggs.checks import *

class TestCheckCoordRange(TestDict):
    '''Test fof Checking Cooridnate Ranges'''
    @pytest.fixture(autouse=True)
    def _set_bad_coords(self):
        self._bad_coords = \
            [(-180.0, 86.0), (180.0, 86.0), (-180.0, -86.0), (180.0, -86.0),
            (-189.0, -84.0), (189.0, -84.0), np.array([0.0, 0.0])]

    def test_check_coord_range_valid(self):
        results = [check_coord_range(c) for c in self._test_dict[6]['geos']]
        assert(all(results)), 'check_coord_range failed for valid geographic coordinates'

    def test_check_coord_range_invalid(self):
        results = [check_coord_range(c) for c in self._bad_coords]
        assert(
            not all(results)
        ), 'check_coord_range failed to detect invalid geographic cooridnates'

    def test_check_coords_range_valid(self):
        results = check_coords_range(self._test_dict[1]['geos'])
        assert(results), 'check_coords_range failed for valid coordinate range'

    def test_check_coords_range_invalid(self):
        results = check_coords_range(self._bad_coords)
        assert(not results), 'check_coords_range failed to detect invalid coordinates'

    def test_validate_coords_lon_lat_valid(self):
        results = validate_coords_lon_lat(self._test_dict[3]['geos'])
        assert(results[0]), 'validate_coords_lon_lat failed for valid geographic cooridnates'

    def test_validate_coords_lon_lat_invalid(self):
        results = validate_coords_lon_lat(self._bad_coords)
        assert(
            not results[0]
        ), 'validate_coords_lon_lat failed to detecte invalid geographic cooridinates'

class TestCheckLevel:
    '''Tests for checking the grid levels'''
    @pytest.fixture(autouse=True)
    def _set_bad_levels(self):
        self._bad_levels = \
            [7, 'L0', 'L6', 'Level', '1', '0']
    def test_check_level_valid(self):
        valid = list(levels_specs.keys())
        results = [check_level(lv) for lv in valid]
        assert(all(results)), 'check_level failed for valid levels'

    def test_check_level_valid_invalid(self):
        results = [check_level(lv) for lv in self._bad_levels]
        assert(not all(results)), 'check_level failed to detect invalid levelts'

class TestCheckGidFormat(TestDict):
    '''Tests for Checking the Grid ID Formating'''

    @pytest.fixture(autouse=True)
    def _set_bad_gids(self):
        self._bad_gids = [
            'L6.405000.30.20.20.90.90', 'L0.405000.30.20.20.90.90.90', 'L0.500999',
            'L6.405000302020909090', 6405000302020909090
        ]

    def test_check_gid_format_valid(self):
        results = [check_gid_format(gid) for gid in self._test_dict[3]['grid_ids']]
        assert(all(results)), 'check_gid_format faild for valid grid IDs'

    def test_check_gid_format_invalid(self):
        results = [check_gid_format(gid) for gid in self._bad_gids]
        assert(not all(results)), 'check_gid_format failed to detect invalid grid IDs'

    def test_check_grid_ids_format_valid(self):

        results = check_grid_ids_format(self._test_dict[2]['grid_ids'])
        assert(results), 'check_grid_ids_format failed for valid grid IDs'

    def test_check_grid_ids_format_invalid(self):
        results = check_grid_ids_format(self._bad_gids)
        assert(not results), 'check_grid_ids_format failed to detect invalid coordinates'

class TestCheckGid(TestDict):
    @pytest.fixture(autouse=True)
    def _set_bad_indicies(self):
        self._bad_indicies =  ['L0.-000000', 'L0.999999', 'L0.406964', 405963]

    @pytest.fixture(autouse=True)
    def _set_bad_elements(self):
        self._bad_elements = [
            'L6.405000.30.20.20.90.90', 'L0.405000.30.20.20.90.90.90', 6405000302020909090
        ]

    @pytest.fixture(autouse=True)
    def _set_bad_gid(self):
        self._bad_gid = ['l0.000000', '0.100555', 123456]

    def test_check_gid_l0_index_valid(self):
        results = [check_gid_l0_index(gid) for gid in self._test_dict[0]['grid_ids']]
        assert(all(results)), 'check_gid_l0_index failed for valid grid indicies'

    def test_check_gid_l0_index_invalid(self):
        results = [check_gid_l0_index(gid) for gid in self._bad_indicies]
        assert(not all(results)), 'check_gid_l0_index failed to detect invalid grid indicies'

    def test_check_grid_ids_l0_index_valid(self):
        results = check_grid_ids_l0_index(self._test_dict[0]['grid_ids'])
        assert(results), 'check_grid_ids_l0_index falied for valid grid IDs'

    def test_check_grid_ids_l0_index_invalid(self):
        results = check_grid_ids_l0_index(self._bad_indicies)
        assert( not results), 'check_grid_ids_l0_index failed to detect invalid grid indicies'

    def test_check_gid_num_elements_valid(self):
        valid = [self._test_dict[lv]['grid_ids'][0] for lv in list(levels_specs.keys())]
        results = [check_gid_num_element(gid) for gid in valid]
        assert(all(valid)), 'check_gid_num_element failed for valid grid IDs'

    def test_check_gid_num_elements_invalid(self):
        results = [check_gid_num_element(gid) for gid in self._bad_elements]
        assert(not all(results)), 'check_gid_l0_index failed to detect invalid grid indicies'

    def check_grid_ids_num_elements_valid(self):
        valid = [self._test_dict[lv]['grid_ids'][0] for lv in list(levels_specs.keys())]
        results = check_grid_ids_num_elements(valid)
        assert(results), 'check_grid_ids_num_elements failed for valid grid IDs'

    def check_grid_ids_num_elements_invalid(self):
        results =  check_grid_ids_num_elements(self._bad_elements)
        assert(not results), 'check_grid_ids_num_elements failed to detect invalid grid IDs'

    def test_check_gid_start_with_valid(self):
        valid = self._test_dict[0]['grid_ids'][0:3]
        results = [check_gid_start_with(gid) for gid in valid]
        assert(all(valid)), 'check_gid_start_with failed for valid grid IDs'

    def test_check_gid_start_with_invalid(self):
        results = [check_gid_start_with(gid) for gid in self._bad_gid]
        assert(not all(results)), 'check_gid_start_with failed to detect invalid grid IDs'

    def test_check_gids_start_with_valid(self):
        results = check_grid_ids_starts_with(self._test_dict[1]['grid_ids'][0:3])
        assert(results), 'check_gids_start_with failed for valid grid IDs'

    def test_check_gids_start_with_invalid(self):
        results = check_grid_ids_starts_with(self._bad_gid)
        assert(not results), 'check_gid_start_with failed to detect invalid grid IDs'

    def test_validate_grid_ids_valid(self):
        valid = [self._test_dict[lv]['grid_ids'][0] for lv in list(levels_specs.keys())]
        results = validate_grid_ids(valid)
        assert(results[0]), 'validate_grid_ids failed for valid grid IDs'

    def test_validate_grid_ids_invalid(self):
        results = validate_grid_ids(self._bad_gid)
        assert(not results[0]), 'validate_grid_ids faile to detect invalid grid IDS'
