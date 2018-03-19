import pytest

from gff2neo.cli import quick_go
from gff2neo.quickgo import fetch_quick_go_data, query_quickgo


def test_fetch_quick_go_id():
    with pytest.raises(ValueError):
        fetch_quick_go_data(quick_go, None)
        fetch_quick_go_data(quick_go, "0005886")


def test_fetch_quick_go_data():
    result = fetch_quick_go_data(quick_go, "GO:0005886")
    assert isinstance(result, list) is True


def test_query_quickgo():
    result = query_quickgo("GO:0005886,GO:0046872,GO:0016301")
    assert result.status_code == 200
