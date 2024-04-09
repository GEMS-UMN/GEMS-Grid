'''
Test for GEMS Grid DGGS Indexing functions.

© Regents of the University of Minnesota. All rights reserved.
This software is released under an Apache 2.0 license. Further details about the Apache 2.0 license are available in the license.txt file.
'''

import pytest
import numpy as np
from geopandas import GeoSeries

from shapely.geometry import Point

from tests.conftest import TestDict, ValidGems
from gemsgrid.constants import grid_spec, levels_specs, cell_scale_factors

from gemsgrid.dggs.utils import shift_range_ease, shift_range_grid_xy, shift_range_grid_multiple
from gemsgrid.dggs.transforms import coords_lon_lat_to_coords_ease, coords_ease_to_coords_grid, \
    grid_xy_coord_to_ease_coord

from gemsgrid.dggs.grid_addressing import geos_to_grid_ids, grid_ids_to_geos, grid_ids_to_ease,  \
        _gid_to_coord_ease, _grid_xy_to_grid_id, ease_polygon_to_grid_ids, geo_polygon_to_grid_ids

'''
Each of the grid_id, centroids, and geos sets below corresponds with
    the following diagram. There are 4 cell from each quadrent
    that make up the test/validation set. The centroids for each of the grid
    cells is easy to calculate manually, and those calculations are
    in generate_pytest_input_responses.ipynb

By manually deriving both the EASE cooridnates and GEMG Grid IDS,
    it also served as an independent validation of the library algorithms.
    Previously, I was using the lib functions, or new independent function to
    try and derive the test/validation sets. This proved more reliable


      min_x                   0                    max_x
max_y +------------------------+------------------------+
      |0|                    |1|2|                    |3|
      |                        |                        |
      |                        |                        |
      |4|                    |5|6|                    |7|
   0  +------------------------+------------------------+
      |8|                    |9|10|                  |11|
      |                        |                        |
      |                        |                        |
      |12|                  |13|14|                  |15|
min_y +------------------------+------------------------+

'''

class TestGeosToGridIds(TestDict):
    def test_geos_to_grid_ids(self):
        '''
        This tests the conversion of the geographic coordintes to grid ID values.
        Each of the seven levels is tested, and all Levels must match
        '''
        for lv,_ in self._test_dict.items():
            valid = self._test_dict[lv]['grid_ids']
            result = geos_to_grid_ids(coords_lon_lat = self._test_dict[lv]['geos'], level = lv)
            assert isinstance(result, dict), 'geo_to_grid did not return a dict'

            if result['success']:
                # all_results[lv] = result['result']['data']
                assert (valid == result['result']['data']), \
                    'geo_to_grid did not return expected grid IDs for level {}'.format(lv)

class TestGridIdsToGeos(TestDict):
    def test_grid_ids_to_geos(self):
        '''
        Test the conversion of grid IDs to geographic cooridnates. All seven levels
            of grid ID are tested, and all should return the the test centroid
            coordinates. Anything past ~ 7 significant figures is noise here, so
            make sure they match to 7 figures
        '''
        sf = 6

        for lv,_ in self._test_dict.items():
            valid = np.array(self._test_dict[lv]['geos'])
            result = grid_ids_to_geos(grid_ids = self._test_dict[lv]['grid_ids'])
            assert isinstance(result, dict), 'grid_ids_to_geo did not return a dict'

            if result['success']:
                assert (np.allclose(valid, np.array(result['result']['data']), rtol = sf ) ), \
                    'geo_to_grid did not return expected grid IDs for level {}'.format(lv)

class Test_GidToCoordEase(TestDict):
    def results(self):
        return [_gid_to_coord_ease(gid) for gid in self._test_dict[0]['grid_ids']]

    def test__gid_to_coord_ease_valid(self):
        sf = 5
        valid = [Point(c[0], c[1]) for c in self._test_dict[0]['centroids']]
        comp = [np.allclose(valid[i].xy, self.results()[i].xy, rtol = sf) for i in range(len(valid))]
        comp = np.array(comp)
        assert(comp.all()), '_gid_to_coord_ease failed to return valid EASE coordinates'

    def test__gid_to_coord_ease_type(self):
        for r in self.results():
            assert( isinstance(r, Point)),'_gid_to_coord_ease did not return correct type'

    def test__gid_to_coord_ease_type(self):
        results = [_gid_to_coord_ease(gid) for gid in [123456]]
        print(results)
        assert(not all(results)), '_gid_to_coord_ease failed to detect invalid input type'

class TestGridIdsToEase(TestDict):
    def test_grid_ids_to_ease_valid(self):
        sf = 5

        valid = np.around(np.array(self._test_dict[0]['centroids']), sf)
        valid = [Point(x[0], x[1]) for x in valid]
        valid = GeoSeries(valid, crs = 6933)

        results = grid_ids_to_ease(self._test_dict[0]['grid_ids'])
        assert all(x == True for x in valid.geom_almost_equals(results, decimal=5)) == True, \
            'grid_ids_to_ease failed to return valid EASE coordinates'

    def test_grid_ids_to_ease_invalid(self):
        results = grid_ids_to_ease('L0.12345')
        assert (not (results)), 'grid_ids_to_ease failed to return invalid EASE cooridnates'

class Test_GridXYToGridId(TestDict,ValidGems):
    def test__grid_xy_to_grid_id_type(self):

        results = [_grid_xy_to_grid_id(t) for t in self._valid_gems]
        assert(not all(results)), '_grid_xy_to_grid_id failed to identify wrong input type '

    def test__grid_xy_to_grid_id_incorrect(self):
        test = [Point(pt[0], pt[1]) for pt in self._valid_gems]
        results = [_grid_xy_to_grid_id(pt) for pt in test ]
        assert(results == self._test_dict[0]['grid_ids']), \
            '_grid_xy_to_grid_id returned incorrect grid IDs'

        for r in results:
            assert isinstance(r, str), '_grid_xy_to_grid_id failed to return str'

class TestPolygonsToGridIds(object):

    @pytest.fixture(autouse=True)
    def _set_polygon(self):
        self._polygon = {
            'ease': 'POLYGON (( \
                0.0000000000000000 -36032.2208400000017718, \
                -36032.2208400000017718 -36032.2208400000017718, \
                -36032.2208400000017718 0.0000000000000000, \
                -36032.2208400000017718 36032.2208400000017718, \
                0.0000000000000000 36032.2208400000017718, \
                36032.2208400000017718 36032.2208400000017718, \
                36032.2208400000017718 0.0000000000000000, \
                36032.2208400000017718 -36032.2208400000017718, \
                0.0000000000000000 -36032.2208400000017718 \
            ))',
            'geo' : 'POLYGON (( \
                0.0000000000000000 -0.2824444146154666, \
                -0.3734439833964395 -0.2824444146154666, \
                -0.3734439833964395 0.0000000000000000, \
                -0.3734439833964395 0.2824444146154666, \
                0.0000000000000000 0.2824444146154666, \
                0.3734439833964395 0.2824444146154666, \
                0.3734439833964395 0.0000000000000000, \
                0.3734439833964395 -0.2824444146154666, \
                0.0000000000000000 -0.2824444146154666 \
            ))'
        }

    @pytest.fixture(autouse=True)
    def _set_valid_ids(self):
        self._valid_ids = ['L0.202481', 'L0.202482', 'L0.203481', 'L0.203482']

    def test_ease_polygon_to_grid_ids(self):

        results = ease_polygon_to_grid_ids(self._polygon['ease'])
        assert(
            results['result']['data'] == self._valid_ids
        ), 'ease_polygone_to_grid_ids failed to return all children within EASE polygon'

    def test_geo_polygon_to_grid_ids(self):

        results = geo_polygon_to_grid_ids(self._polygon['geo'])
        assert(
            results['result']['data'] == self._valid_ids
        ), 'geo_polygone_to_grid_ids failed to return all children within geographic polygon'
