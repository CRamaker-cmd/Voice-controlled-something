from macrovoice.units import UnitKind, to_grams


def test_mass_and_volume_need_no_product_data():
    assert to_grams(2, UnitKind.MASS, 1000, None, None) == (2000, None)
    assert to_grams(250, UnitKind.VOLUME, 1, None, None) == (250, None)


def test_serving_and_package_use_product_sizes():
    assert to_grams(3, UnitKind.SERVING, 1, 35, None) == (105, None)
    assert to_grams(2, UnitKind.PACKAGE, 1, None, 800) == (1600, None)


def test_missing_sizes_are_reported_not_guessed():
    grams, reason = to_grams(1, UnitKind.SERVING, 1, None, 800)
    assert grams is None and "serving size" in reason
    grams, reason = to_grams(1, UnitKind.PACKAGE, 1, 35, None)
    assert grams is None and "package size" in reason
    assert to_grams(1, UnitKind.MEASURE, 1, 35, 800)[0] is None
