"""
Interface to the quickGO interface.
"""
from __future__ import print_function

from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://www.ebi.ac.uk/QuickGO/services"


# def fetch_quick_go_data(quick_go, go_id):
#     """
#     Retrieve information given a GO identifier.
#     :param quick_go:
#     :param go_id:
#     :return:
#     """
#     go_is_a = []
#     if go_id and go_id.startswith("GO:"):
#         result = quick_go.Term(go_id, frmt="obo")
#         if result and not isinstance(result, int):
#             for res in result.split('\n'):
#                 if 'is_a' in res:
#                     go_is_a.append(res)
#     else:
#         raise ValueError("GO id can't be: {}".format(go_id))
#     return go_is_a


def query_quickgo(go_term_ids):
    """
    Retrieve information given a GO identifiers.
    :param str go_term_ids:
    :return:
    """
    s = Session()
    s.mount(BASE_URL, HTTPAdapter(
        max_retries=Retry(total=10, backoff_factor=0.2, status_forcelist=[500])
    ))
    url = BASE_URL + "/ontology/go/terms/"
    headers = {'Accept': 'application/json'}
    res = s.get(url + go_term_ids, headers=headers)
    return res
