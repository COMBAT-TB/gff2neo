"""Fetching data from STRING and STITCH
"""
import requests
from pandas import read_csv
from requests.exceptions import ConnectionError, HTTPError
from tqdm import tqdm

from tb2neo.dbconn import graph
from tb2neo.uniprot import UNIPROT_DATA, eu_mapping

STRING_API_URL = "https://string-db.org/api"
STITCH_API_URL = "http://stitch.embl.de/api"
TAXON_ID = "83332"


def create_ppi(rv_a, rv_b, score):
    cypher_q = f"MATCH (ga {{ uniquename: '{rv_a}' }})--(ap:Protein),"
    cypher_q += f"(gb {{ uniquename: '{rv_b}' }})--(bp:Protein) "
    cypher_q += f"CREATE UNIQUE "
    cypher_q += f"(ap)-[r:INTERACTS_WITH {{ score: {score} }}]->(bp)"
    data = graph.run(cypher_q).data()
    return data


def fetch_string_data(gene, output_format='json', method='network',
                      taxon=TAXON_ID):
    # This is interesting
    # https://string-db.org/api/json/network?identifiers=None&species=83332
    request_url = STRING_API_URL + "/" + output_format + "/" + method + "?"
    request_url += f"identifiers={gene}"
    request_url += "&" + f"species={TAXON_ID}"
    result = None
    try:
        response = requests.get(request_url)
    except (HTTPError, ConnectionError) as error:
        print(f'An error occured for {gene}:\n{error}')
    except Exception as e:
        print(f'There was an exception for {gene}:\n{e}')
    else:
        if response.status_code == 200:
            result = response.json()
    return result


def load_string_data():
    df = read_csv(UNIPROT_DATA).fillna("")
    for entry in tqdm(df.values):
        uniprot_id = str(entry[0]).strip()
        rv_tag = eu_mapping(from_=uniprot_id, to='TUBERCULIST_ID')
        gene = rv_tag[0] if rv_tag else None
        data = fetch_string_data(gene=gene) if gene else None
        if data:
            for ppi in data:
                create_ppi(ppi["stringId_A"], ppi["stringId_B"], ppi["score"])
        else:
            print(f"Nothing found for {rv_tag} with entry: {uniprot_id}")


def fetch_stitch_data():
    pass
