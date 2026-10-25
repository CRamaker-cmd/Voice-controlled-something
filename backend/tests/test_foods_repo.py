from macrovoice.foods import FoodRecord, FoodRepo, fts_query, stem, tokenize


def rec(**kw):
    base = dict(source="off", source_id="x", name="Skyr", kcal_100g=60, protein_100g=10, carbs_100g=4, fat_100g=0.2)
    return FoodRecord(**{**base, **kw})


def test_upsert_is_idempotent_and_updates(conn):
    repo = FoodRepo(conn)
    a = repo.upsert(rec(kcal_100g=60))
    b = repo.upsert(rec(kcal_100g=70))
    assert a == b and repo.count() == 1 and repo.get(a).kcal_100g == 70


def test_search_requires_all_tokens_and_matches_brand(conn):
    repo = FoodRepo(conn)
    repo.upsert(rec(source_id="1", name="Skyr naturel", brand="Jumbo"))
    repo.upsert(rec(source_id="2", name="Skyr vanille", brand="Albert Heijn"))
    assert [f.name for f in repo.search(["jumbo", "skyr"])] == ["Skyr naturel"]
    assert repo.search(["jumbo", "vanille"]) == []
    assert repo.search([]) == []


def test_search_handles_plurals_prefixes_and_diacritics(conn):
    repo = FoodRepo(conn)
    repo.upsert(rec(source_id="1", name="Banana"))
    repo.upsert(rec(source_id="2", name="Crème fraîche"))
    assert repo.search(["bananas"]) and repo.search(["banan"]) and repo.search(["creme", "fraiche"])


def test_fts_stays_in_sync_after_update_and_delete(conn):
    repo = FoodRepo(conn)
    fid = repo.upsert(rec(name="Old name"))
    repo.upsert(rec(name="New name"))
    assert repo.search(["old"]) == [] and len(repo.search(["new"])) == 1
    with conn:
        conn.execute("DELETE FROM foods WHERE id = ?", (fid,))
    assert repo.search(["new"]) == []


def test_source_rank_prefers_manual_over_off_over_ai(conn):
    repo = FoodRepo(conn)
    repo.upsert(rec(source="ai", source_id="a", name="Skyr"))
    repo.upsert(rec(source="off", source_id="o", name="Skyr"))
    repo.upsert(rec(source="manual", source_id="m", name="Skyr"))
    assert [f.source for f in repo.search(["skyr"])] == ["manual", "off", "ai"]


def test_brand_lookup_uses_the_brand_index(conn):
    repo = FoodRepo(conn)
    repo.upsert(rec(brand="Jumbo"))
    assert len(repo.by_brand("jumbo")) == 1
    plan = conn.execute("EXPLAIN QUERY PLAN SELECT * FROM foods WHERE brand = ? COLLATE NOCASE", ("x",)).fetchall()
    assert any("idx_foods_brand" in r["detail"] for r in plan)


def test_query_helpers():
    assert tokenize("AH Volkoren-brood!") == ["ah", "volkoren", "brood"]
    assert stem("eggs") == "egg" and stem("berries") == "berry" and stem("glass") == "glass"
    assert fts_query(["bananas"]) == '("bananas"* OR "banana"*)'
