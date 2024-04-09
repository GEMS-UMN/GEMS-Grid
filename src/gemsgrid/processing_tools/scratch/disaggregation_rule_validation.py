'''
This module has the rule validation for disaggregation functions.

© Regents of the University of Minnesota. All rights reserved.
This software is released under an Apache 2.0 license. Further details about the Apache 2.0 license are available in the license.txt file.
'''
import numpy as np
import re


def range_overlap(range1, range2):
    '''
    Test if two ranges overlap.

    Parameters
    ----------
    range1: numpy.ndarray with two values representing a range of a rule
    range2: numpy.ndarray with two values representing a range of a rule

    Returns
    -------
    Nothing, can print or raise a warning if ranges overlap
    '''

    x1, x2 = range1.min(), range1.max()
    y1, y2 = range2.min(), range2.max()

    if x1 <= y2 and y1 <= x2:
        print(f'Warning: rule {x1, x2} conflicts with rule {y1, y2}')


def not_eq_split(splits, dif):
    '''
    Takes a list of at least 3 values where the smallest and largest values are <, >, <=, or >= rules. The rules
    inbetween these values are != rules.

    Parameters
    ----------
    splits: List. A list of at least 3 values forming rules.
    dif: Float. A small value, typically around 0.00001, used to create rules on either side of a != rule. For example,
        the rules <=4, !=7, <=9 becomes [4 to 6.99999] [7.00001 to 9]

    Returns
    -------
    List. A list of numpy nd.arrrays representing ranges of rules.
    '''

    reserved = []
    for n in range(0, len(splits) - 1):
        # Make ndarrays of length 2 with values from splits list
        # Add or subtact 'dif' value for rules in the middle because they are != rules
        if n == 0:
            pair_range = np.linspace(splits[n], splits[n + 1] - dif, 2)
        elif 0 < n < len(splits) - 2:
            pair_range = np.linspace(splits[n] + dif, splits[n + 1] - dif, 2)
        elif n == len(splits) - 2:
            pair_range = np.linspace(splits[n] + dif, splits[n + 1], 2)
        reserved.append(pair_range)
    return reserved


def parse_rule(rule):
    '''
    Takes the value for a single key of a dictionary that defines mask rules and converts it into a list of ranges
    representing the values effected by a rule. Because we are only interested in if more than one rule applies to
    the same value, we can ignore boolean operators and evaluate each rule independently. All <, >, <=, and >= based
    rules and appended together, sorted, and then paired together, so the order of rules does not matter. If there
    are an unequal number of >/>= and </<= rules, this implies that and unbounded range rule was created, so a max or
    min value for the 32-bit float data type to add a bound.

    Parameters
    ----------
    rule: String. Must match pattern of: (mask{equality operator}{float or int rule value})

    Returns
    -------

    '''
    not_eq_dif = 0.00001  # A small value, typically around 0.00001, used to create rules on either side of a != rule
    data_type_max = 340282370000000000000000000000000000000
    data_type_min = -340282370000000000000000000000000000000
    reserved, not_eq, gt, lt = [], [], [], []  # Empty lists for parsed rules, !=, >/>=, and </<=

    rule = rule.replace(" ", "")
    # equality_rules = re.findall('\(mask==(.*?)\)', rule)
    equality_rules = re.findall('\(mask==([+-]?([0-9]*[.])?[0-9]+)\)', rule)
    for substr in equality_rules :
        eq_range = np.linspace(float(substr[0]), float(substr[0]), 2)
        reserved.append(eq_range)

    not_eq_rules = re.findall('\(mask!=([+-]?([0-9]*[.])?[0-9]+)\)', rule)
    for substr in not_eq_rules :
        not_eq.append(float(substr[0]))

    gt_rules = re.findall('\((mask>=?([+-]?([0-9]*[.])?[0-9]+))\)', rule)
    for substr in gt_rules:
        if '=' in substr[0]:
            gt.append(float(substr[1]))
        else:
            # if rule is >, add a small dif factor so it does not conflict with rules with = operator
            gt.append(float(substr[1]) + not_eq_dif)

    lt_rules = re.findall('\((mask<=?([+-]?([0-9]*[.])?[0-9]+))\)', rule)
    for substr in lt_rules:
        if '=' in substr[0]:
            lt.append(float(substr[1]))
        else:
            # if rule is <, subtract a small dif factor so it does not conflict with rules with = operator
            lt.append(float(substr[1]) - not_eq_dif)

    # Compares the length of the >/>= and </<= rules lists. If they are within 1 of each other, it indicates one of the
    # rules is unbounded (i.e., >=150, with no rules on values above 150). In this case the max or min value of the data
    # type is added to create a range. If they are more than 1 apart, then ranges overlap and it raises an exception.
    if len(gt) - len(lt) == 1:
        gt.append(data_type_max)
    elif len(gt) - len(lt) == -1:
        lt.append(data_type_min)
    elif len(gt) - len(lt) != 0:
        raise Exception(f'Overlapping ranges in {rule}')

    all_rules = gt + lt
    all_rules.sort()  # create a sorted list of rule values

    # Iterate through pairs of rules and converts them to a list of ranges
    for i in range(0, len(all_rules), 2):
        splits = []
        not_eq_copy = not_eq.copy()  # Create a copy because not_eq will be modified in the loop below.
        # This loop handles cases where there are multipe != rules within a single range by appending them to a list
        # to convert into rules below.
        for val in not_eq_copy:
            if val > all_rules[i] and val < all_rules[i+1]:
                splits.append(val)
                not_eq.remove(val)

        splits.sort()
        if len(splits) == 0:  # Usually there are no != rules in a range and it can just be converted to a range as is
            pair_range = np.linspace(all_rules[i], all_rules[i+1], 2)
            reserved.append(pair_range)
        else:  # If there is one or more != in a pair range, the !=, >/>=, and </<= rules are sent to not_eq_split
            splits.extend([all_rules[i], all_rules[i + 1]])
            splits.sort()
            reserved = reserved + not_eq_split(splits, not_eq_dif)

    # The block below handles any != rules not between >/>= and </<= rules.
    if len(not_eq)> 0:
        for val in not_eq:
            splits = not_eq + [data_type_min, data_type_max]
            splits.sort()
            reserved = reserved + not_eq_split(splits, not_eq_dif)
    return reserved


def run_test_rules(categories_dict):
    '''
    Function for looping through a dictionary of mask rules, sending rules to the parse_rule function and collecting the
    returned ranages from each rule. It then sends all combinations of rules to the range_overlap test function.

    Parameters
    ----------
    categories_dict: Dictionary. Format must match the mask creation dictionary.

    Returns
    -------
    Nothing, if rule overlap is detected, the rules will be printed or an exception will be raised.
    '''
    rule_ranges = []
    for key, value in categories_dict.items():
        rule_range = parse_rule(value[0])
        rule_ranges.append(rule_range)

    flat_rules = [item for sublist in rule_ranges for item in sublist]  # Flatten the returned list of lists
    print(flat_rules)

    # Compare all combinations of rules
    for r1_index, rule1 in enumerate(flat_rules):
        for r2_index, rule2 in enumerate(flat_rules):
            if r2_index < r1_index: #  This prevents comparing a rule to itself, and duplicate comparisons
                range_overlap(rule1, rule2)



# cat_dict = {1 : ["(mask == 1) | (mask == 2)", 40], 2: ["(mask == 45) | (mask == 4) | (mask == 5)", 50], 3: ["(mask<-67.6) & (mask < -12.5) & (mask>=-22.3) & (mask>91.2) & (mask>=67.6) & (mask!=90)", 10]}
#cat_dict = {1 : ["(mask == 1)", 40], 2: ["(mask == 7) | (mask == 4) | (mask == 5)", 50], 3: ["(mask>9.6) & (mask <12.5) & (mask>=22.3) & (mask<=53.6) & (mask>=67.6) & (mask!=90)& (mask!=95)& (mask<150)" , 10]}
# cat_dict = {1 : ["(mask == 1) | (mask == 2)", 40], 2: ["(mask == -90) | (mask == 4) | (mask > 5)", 50], 3: ["(mask> 67.6)", 10]}
# cat_dict = {1 : ["(mask == 1) | (mask == 2)", 40], 2: ["(mask == -90) | (mask == 4) | (mask == 5)", 50], 3: ["(mask< 67.6) & (mask >= 5.5) & (mask!=5) & (mask!=9)", 10]}
# cat_dict = {1 : ["(mask == 1) | (mask == 2)", 40], 2: ["(mask == -90) | (mask == 4) | (mask == 5)", 50], 3: ["(mask< 67.6) & (mask >= 5.5) & (mask!=5) & (mask!=9)", 10]}


#cat_dict = {1 : ["(mask >= 7)", 40], 2 : ["(mask != 5.8) & (mask > 4)", 60]}
cat_dict = {1 : ["(mask <= 7) | (mask >= 1)", 40], 2 : ["(mask >= 1)", 60]}
run_test_rules(cat_dict)

