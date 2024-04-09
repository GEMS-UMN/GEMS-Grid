'''
Tests for GEMS Grid hierarchy.

© Regents of the University of Minnesota. All rights reserved.
This software is released under an Apache 2.0 license. Further details about the Apache 2.0 license are available in the license.txt file.
'''
# from tests.config import dumb_test, test_dict
import pytest
from pytest import approx

from tests.conftest import TestDict

from gemsgrid.dggs.hierarchy import _child_to_parent, children_to_parents, \
    grid_aggregate, _parent_to_children, parents_to_children

class TestParentChildRelations(TestDict):
    valid_children = [
        [
            'L1.000000.00',  'L1.000000.01', 'L1.000000.02','L1.000000.03',
            'L1.000000.10', 'L1.000000.11', 'L1.000000.12','L1.000000.13',
            'L1.000000.20', 'L1.000000.21', 'L1.000000.22', 'L1.000000.23',
            'L1.000000.30', 'L1.000000.31', 'L1.000000.32', 'L1.000000.33'
        ],
        [
            'L1.000481.00', 'L1.000481.01', 'L1.000481.02','L1.000481.03',
            'L1.000481.10', 'L1.000481.11', 'L1.000481.12', 'L1.000481.13',
            'L1.000481.20', 'L1.000481.21','L1.000481.22', 'L1.000481.23',
            'L1.000481.30', 'L1.000481.31','L1.000481.32', 'L1.000481.33'
        ]
    ]

    def test__child_to_parent_valid_parents(self):
        results = [_child_to_parent(c) for c in self._test_dict[1]['grid_ids']]
        assert(
            results == self._test_dict[0]['grid_ids']
        ), '_child_to_parent failed to return valid parent IDs for children'

    def test__child_to_parent_invalid_parents(self):
        results = [_child_to_parent(c) for c in self._test_dict[0]['grid_ids']]
        assert(
            not all(results)
        ), '_child_to_parent returned valid parent IDs for cells without parents '

    def test__child_to_parent_type(self):
        results = [_child_to_parent(c) for c in [123456, 1.123456]]
        assert(not all(results)), '_child_to_parent failed to identify wrong input type'

    def test_children_to_parents_parents(self):
        results = children_to_parents(self._test_dict[1]['grid_ids'])
        assert(
            results['result']['data'] == self._test_dict[0]['grid_ids']
        ), 'children_to_parents failed to return correct parent IDs for children'

    def test_children_to_parents_gridid(self):
        results = children_to_parents(self._test_dict[0]['grid_ids'])
        assert(
            not results['success']
        ), 'children to parents failed to detect incorrect grid ID'

    def test_children_to_parents_types(self):
        results = children_to_parents([123456, 1.123456])
        assert(
            not results['success']
        ), 'childred_to_parents failed to identfy wrong input type'

    def test__parent_to_children_ids(self, valid = valid_children):
        results = _parent_to_children(self._test_dict[0]['grid_ids'][0])
        assert(
            results == valid[0]
        ),  '_parent_to_children failed to return correponding children grid IDs'

    def test__parent_to_children_types(self, valid = valid_children):
        results = _parent_to_children(self._test_dict[0]['grid_ids'][0:2])
        assert(not results), '_parent_to_children failed to identify wrong input type'

    def test_parents_to_children_valid(self, valid = valid_children):
        results = parents_to_children(self._test_dict[0]['grid_ids'][0:2])
        assert(
            results['result']['data'] == valid
        ), 'parents_to_children failed to return corresponding children grid IDs'

    def test_parents_to_children_invalid(self, valid = valid_children):
        results = parents_to_children(self._test_dict[0]['grid_ids'][0])
        assert(
            not results['success']
        ), 'parents_to_children failed to detect invalid input type'

class TestGridAggregate:
    test_set = [
        'L3.048218.20.10.00', 'L3.048218.20.10.01',  'L3.048218.20.10.02',
        'L3.048218.20.10.10', 'L3.048218.20.10.11', 'L3.048218.20.10.12',
        'L3.048218.20.10.20', 'L3.048218.20.10.21', 'L3.048218.20.10.22'
    ]
    test_vals = [1., 1., 1., 2., 3., 4., 5., 6., 7. ]

    valid_agg = {
        'count' : {'grid_ids': ['L2.048218.20.10'], 'values': [9]},
        'first' : {'grid_ids': ['L2.048218.20.10'], 'values': [1.0]},
        'last' : {'grid_ids': ['L2.048218.20.10'], 'values': [7.0]},
        'mean' : {'grid_ids': ['L2.048218.20.10'], 'values': [3.3333333333333335]},
        'median' : {'grid_ids': ['L2.048218.20.10'], 'values': [3.0]},
        'min' : {'grid_ids': ['L2.048218.20.10'], 'values': [1.0]},
        'max' : {'grid_ids': ['L2.048218.20.10'], 'values': [7.0]},
        'std' : {'grid_ids': ['L2.048218.20.10'], 'values': [2.29128784747792]},
        'sum' : {'grid_ids': ['L2.048218.20.10'], 'values': [30.0]},
        'var' : {'grid_ids': ['L2.048218.20.10'], 'values': [5.25]},
        # 'mad' : {'grid_ids': ['L2.048218.20.10'], 'values': [1.9259259259259263]},
        'prod' : {'grid_ids': ['L2.048218.20.10'], 'values': [5040.0]},
        'mode' : {'grid_ids': ['L2.048218.20.10'], 'values': [1.0]},
    }

    def test_grid_aggregate(
        self,
        test={'grid_ids':test_set, 'grid_vals': test_vals},
        valid = valid_agg
    ):
        for method in valid.keys():
            results = grid_aggregate(
                test['grid_ids'],
                test['grid_vals'],
                level = 2,
                method = method
            )
            assert(results['result']['data'] == approx(valid[method])), \
                'Grid aggregation failed for {}'.format(method)

# seems a test for gen_child_geometries was never written originally
#   probably needs rectified at some point
# def test_gen_child_geometries():

#     results =
#     assert()
