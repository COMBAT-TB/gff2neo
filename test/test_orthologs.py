import pytest

from tb2neo.orthologs import fetch_ortholog


def test_fetch_ortholog_error():
    with pytest.raises(ValueError):
        fetch_ortholog()


def test_fetch_ortholog_exception():
    with pytest.raises(Exception):
        fetch_ortholog(locus_tag="Rv0239", tuberculist_url=None)


@pytest.mark.skip(reason="svitsrv8.epfl.ch times out")
def test_fetch_ortholog_result():
    result = fetch_ortholog(locus_tag="Rv0239")
    # assert isinstance(result, unicode) is True
    assert result == 'MT0253'
