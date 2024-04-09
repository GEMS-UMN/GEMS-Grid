'''
Tests for GEMS Grid DGGS grid_transform fucntions.

© Regents of the University of Minnesota. All rights reserved.
This software is released under an Apache 2.0 license. Further details about the Apache 2.0 license are available in the license.txt file.
'''
import pytest
import numpy as np
from geopandas import GeoSeries
from shapely.geometry import Point

from tests.conftest import TestDict, ValidGems

from gemsgrid.constants import ease_crs

from gemsgrid.dggs.transforms import *

class TestEaseCoordToGridXYCoord(TestDict):
    def results(self):
        return [ease_coord_to_grid_xy_coord(c[0], c[1]) for c in self._test_dict[0]['centroids']]

    def test_ease_coord_to_grid_xy_coord_valid(self):
        sf = 10
        assert(
            (np.allclose(self.results(), self._test_dict[1]['centroids'], rtol = sf))
        ), 'ease_coord_to_grid_xy_coord did not reutrn valid grid xy coords'

    def test_ease_coord_to_grid_xy_coord_tuples(self):
        for r in self.results():
            #assert(r, tuple), 'ease_coord_to_grid_xy_coord failed to return tuples'
            assert isinstance(r, tuple), 'ease_coord_to_grid_xy_coord failed to return tuples'

    def test_ease_coord_to_grid_xy_coord_type(self):
        results = [
            ease_coord_to_grid_xy_coord(c[0], c[1]) for c in [
                (0, int(1)), (int(5), 4), (int(29), int(460))
            ]
        ]
        assert(not all(results)), 'ease_coord_to_grid_xy_coord failed to identify bad input types'

class TestGridXYToEaseCoord(TestDict, ValidGems):
    def results(self):
        return [grid_xy_coord_to_ease_coord(c[0], c[1]) for c in self._valid_gems]

    def test_grid_xy_to_ease_coord_valid(self):
        sf = 6
        assert(
            np.allclose(self.results(), self._test_dict[1]['centroids'], rtol = sf)
        ), 'ease_coord_to_grid_xy_coord failed to return valid ease coords'

    def test_grid_xy_to_ease_coord_tuples(self):
        for r in self.results():
            #assert(r, tuple), 'grid_xy_to_ease_coord failed to return tuples'
            assert isinstance(r, tuple), 'grid_xy_to_ease_coord failed to return tuples'

    def test_grid_xy_to_ease_coord_types(self):
        results = [
            grid_xy_coord_to_ease_coord(c[0], c[1]) for c in [
                (0, int(1)), (int(5), 4), (int(29), int(460))
            ]
        ]
        assert(not all(results)), 'grid_xy_to_ease_coord failed to identify bad input types'

class TestCoordEaseToCoordsGrid(TestDict, ValidGems):
    def results(self):
        return coords_ease_to_coords_grid(self._valid_gems)

    def results_gs(self):
        geom = [Point(pt[0], pt[1]) for pt in self._test_dict[0]['centroids']]
        test_gs = GeoSeries(geom, crs=ease_crs)

        return coords_ease_to_coords_grid(test_gs, level=0)

    def test_coords_ease_to_coords_grid_type(self):
        assert (
            not self.results()
        ), 'coords_ease_to_coords_grid failed to detect incorrect input type'

    def test_coords_ease_to_coords_grid_geoseries(self):
        assert (
            isinstance(self.results_gs(), GeoSeries)
        ), 'coords_ease_to_coords_grid did not return a GeoSeries'

    def test_coords_ease_to_coords_grid_invalid(self):
        sf = 6
        valid = np.array(self._valid_gems)
        result =[np.array((geom.xy[0][0], geom.xy[1][0])) for geom in self.results_gs()]
        result = np.array(result)
        assert (
            np.allclose(valid, result, rtol = sf)
        ), 'coords_ease_to_coords_grid returned incorrect GEMS grid points'

class TestCoordLonLatToCoordsEase(TestDict):
    def results(self):
        return coords_lon_lat_to_coords_ease(self._test_dict[1]['geos'])

    def test_coords_lon_lat_to_coords_ease_geoseries(self):
        assert(isinstance(self.results(), GeoSeries)), \
            'coords_lon_lat_to_coords_ease failed to return GeoSeries'

    def test_coords_lon_lat_to_coords_ease_valid(self):
        sf = 5
        results = self.results().apply(lambda r: np.asarray([r.x, r.y]))
        results = np.stack(results)
        assert(
            (np.allclose(results, self._test_dict[1]['centroids']))
        ), 'coords_lon_lat_to_coords_ease failed to return valid EASE coords'

    def test_coords_lon_lat_to_coords_ease_type(self):
        results = coords_lon_lat_to_coords_ease((-150.5,-62.6))
        assert(
            not results
        ), 'coords_lon_lat_to_coords_ease failed to detect incorrect input type'

