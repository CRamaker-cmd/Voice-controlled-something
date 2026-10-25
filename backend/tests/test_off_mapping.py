from macrovoice.ingest.off import product_to_record
from macrovoice.ingest.pipeline import sane
from conftest import OFF_PRODUCTS


def test_maps_a_full_product():
    r = product_to_record(OFF_PRODUCTS[0])
    assert (r.source, r.source_id, r.name, r.brand, r.category) == ("off", "1", "Volkoren brood", "Albert Heijn", "wholemeal-breads")
    assert (r.kcal_100g, r.serving_g, r.package_g) == (240, 35.0, 800.0)


def test_first_brand_wins_and_blank_brand_is_none():
    assert product_to_record(OFF_PRODUCTS[1]).brand == "Jumbo"
    assert product_to_record(OFF_PRODUCTS[2]).brand is None


def test_kj_fallback():
    p = {"code": "9", "product_name": "X", "nutriments": {"energy_100g": 418.4, "proteins_100g": 1,
                                                          "carbohydrates_100g": 1, "fat_100g": 1}}
    assert round(product_to_record(p).kcal_100g) == 100


def test_incomplete_products_are_dropped_not_filled_in():
    assert product_to_record({"code": "1", "product_name": "X", "nutriments": {"proteins_100g": 1}}) is None
    assert product_to_record({"product_name": "X", "nutriments": {}}) is None


def test_sanity_filter():
    good = product_to_record(OFF_PRODUCTS[0])
    assert sane(good)
    assert not sane(good.__class__(**{**good.__dict__, "kcal_100g": 5000}))
    assert not sane(good.__class__(**{**good.__dict__, "protein_100g": 80, "carbs_100g": 80}))
    assert not sane(good.__class__(**{**good.__dict__, "fat_100g": float("nan")}))
