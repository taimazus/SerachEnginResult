import pytest

import storage


@pytest.fixture
def database(tmp_path, monkeypatch):
    monkeypatch.setenv("RANK_TRACKER_DB", str(tmp_path / "test.sqlite3"))
    storage.initialize_database()


def test_projects_keywords_and_history_persist(database):
    storage.create_project(" فروشگاه ")
    project = storage.get_projects()[0]
    assert project["name"] == "فروشگاه"

    storage.add_keyword(project["id"], " تعمیر تلویزیون ", "https://Example.ir/path")
    keyword = storage.get_keywords(project["id"])[0]
    assert keyword["query"] == "تعمیر تلویزیون"
    assert keyword["target_domain"] == "example.ir"

    result = {
        "status": "found",
        "rank": 4,
        "result_page": 1,
        "message": "Found",
    }
    storage.save_check(keyword["id"], result)
    assert storage.get_history(keyword["id"])[0]["rank"] == 4


def test_duplicate_project_and_keyword_are_reported(database):
    storage.create_project("store")
    project = storage.get_projects()[0]
    with pytest.raises(ValueError, match="از قبل"):
        storage.create_project("store")

    storage.add_keyword(project["id"], "query", "example.ir")
    with pytest.raises(ValueError, match="قبلاً"):
        storage.add_keyword(project["id"], "query", "example.ir")


def test_empty_inputs_and_nonpositive_history_limit_are_rejected(database):
    with pytest.raises(ValueError):
        storage.create_project(" ")
    storage.create_project("store")
    project = storage.get_projects()[0]
    with pytest.raises(ValueError):
        storage.add_keyword(project["id"], "", "example.ir")
    with pytest.raises(ValueError):
        storage.get_history(1, limit=0)
