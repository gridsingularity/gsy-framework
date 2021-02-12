from deepdiff import DeepDiff


def assert_dicts_identical(dict1, dict2):
    assert len(DeepDiff(dict1, dict2, ignore_order=True)) == 0
