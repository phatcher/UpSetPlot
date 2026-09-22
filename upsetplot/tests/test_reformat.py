import pandas as pd
import pytest
from pandas.testing import assert_frame_equal, assert_series_equal

from upsetplot import from_memberships, generate_counts, generate_samples, query

# `query` is mostly tested through plotting tests, especially tests of
# `_process_data` which cover sort_by, sort_categories_by, subset_size
# and sum_over.


@pytest.mark.parametrize(
    "data",
    [
        generate_counts(),
        generate_samples(),
    ],
)
@pytest.mark.parametrize(
    "param_set",
    [
        [{"present": "cat1"}, {"absent": "cat1"}],
        [{"max_degree": 0}, {"min_degree": 1, "max_degree": 2}, {"min_degree": 3}],
        [{"max_subset_size": 30}, {"min_subset_size": 31}],
        [
            {"present": "cat1", "max_subset_size": 30},
            {"absent": "cat1", "max_subset_size": 30},
            {"present": "cat1", "min_subset_size": 31},
            {"absent": "cat1", "min_subset_size": 31},
        ],
    ],
)
def test_mece_queries(data, param_set):
    unfiltered_results = query(data)
    all_results = [query(data, **params) for params in param_set]

    # category_totals is unaffected by filter
    for results in all_results:
        assert_series_equal(unfiltered_results.category_totals, results.category_totals)

    combined_data = pd.concat([results.data for results in all_results])
    combined_data.sort_index(inplace=True)
    assert_frame_equal(unfiltered_results.data.sort_index(), combined_data)

    combined_sizes = pd.concat([results.subset_sizes for results in all_results])
    combined_sizes.sort_index(inplace=True)
    assert_series_equal(unfiltered_results.subset_sizes.sort_index(), combined_sizes)


def _sizes_by_categories(sizes):
    """Map each subset's categories to its size, for order-free comparison"""
    names = sizes.index.names
    return {
        frozenset(
            name for name, present in zip(names, combo, strict=True) if present
        ): size
        for combo, size in sizes.items()
    }


# One item in each of A only, AB, ABC and none: no item is in exactly AC or BC
ABC_DATA = from_memberships([["A"], ["A", "B"], ["A", "B", "C"], []])


def test_inclusive_subset_sizes():
    results = query(ABC_DATA, subset_size="count")
    sizes = _sizes_by_categories(results.inclusive_subset_sizes)

    assert sizes[frozenset("A")] == 3  # A, AB and ABC
    assert sizes[frozenset("AB")] == 2  # AB and ABC
    assert sizes[frozenset("ABC")] == 1
    assert sizes[frozenset()] == 4  # every item is in at least no categories
    # AC and BC have no items of their own, so are not present at all
    assert frozenset("AC") not in sizes


def test_inclusive_subset_sizes_match_category_totals():
    results = query(generate_counts())
    sizes = _sizes_by_categories(results.inclusive_subset_sizes)

    for category, total in results.category_totals.items():
        assert sizes[frozenset([category])] == total


def test_inclusive_subset_sizes_count_filtered_subsets():
    unfiltered = query(ABC_DATA, subset_size="count")
    # dropping ABC from display should not change what AB counts
    filtered = query(ABC_DATA, subset_size="count", max_degree=2)

    assert _sizes_by_categories(filtered.inclusive_subset_sizes) == {
        categories: size
        for categories, size in _sizes_by_categories(
            unfiltered.inclusive_subset_sizes
        ).items()
        if len(categories) <= 2
    }


@pytest.mark.parametrize("sort_by", ["cardinality", "degree", "input"])
@pytest.mark.parametrize("sort_categories_by", ["cardinality", "input"])
def test_inclusive_subset_sizes_follow_sorting(sort_by, sort_categories_by):
    results = query(
        generate_counts(), sort_by=sort_by, sort_categories_by=sort_categories_by
    )

    assert_frame_equal(
        results.inclusive_subset_sizes.index.to_frame(),
        results.subset_sizes.index.to_frame(),
    )
    # every subset is at least as big counted inclusively
    assert (results.inclusive_subset_sizes >= results.subset_sizes).all()
