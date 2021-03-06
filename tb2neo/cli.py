"""
Cli
"""
import os
import sys

import click

from tb2neo.dbconn import (DRUG_VOCAB, TARGET_PROTEIN_IDS,
                           build_gff_relationships, create_chromosome_nodes,
                           create_drugbank_nodes, create_go_term_nodes,
                           create_kegg_pathways_nodes, create_operon_nodes,
                           create_organism_nodes, create_protein_nodes,
                           create_publication_nodes,
                           create_reactome_pathway_nodes, delete_db_data,
                           graph, map_srna_to_mrna)
from tb2neo.gffproc import (examine_gff_file, get_locus_tags,
                            map_functional_category, parse_gff)
from tb2neo.mutations import process_mutation_file
from tb2neo.stringstitch import load_string_data
from tb2neo.uniprot import UNIPROT_DATA, query_uniprot

CURR_DIR = os.path.dirname(os.path.abspath(__file__))

MYCO_GFF = os.path.join(
    CURR_DIR, "data/myco/Mycobacterium_tuberculosis_H37Rv.gff")
OPERON_DATA = os.path.join(
    CURR_DIR,
    "data/operon/mycobacterium_tuberculosis_h37rv_genome_summary.txt")
SRNA_TXTFILE = os.path.join(
    CURR_DIR, "data/srna/")
DR_DATA_DIR = os.path.join(CURR_DIR, 'data/mutations/')


def check_csv(csvfile):
    """
    Check if csv file exists and is not empty.
    :param csvfile:
    :return:
    """
    try:
        csv_file = open(csvfile, 'r')
    except OSError:
        _file = False
    else:
        csv_file.close()
        _file = True
    return _file


uniprot_config = {
    'h37rv': {'taxonomy': '83332', 'proteome': 'UP000001584'},
    'cdc1551': {'taxonomy': '83331', 'proteome': 'UP000001020'},
}


def get_taxonomy_and_proteome(gff_file):
    """
    Get Taxonomy and Proteome.
    :param gff_file:
    :return:
    """
    result = dict()
    file_name = gff_file.split("/")[-1]
    for k, v in uniprot_config.items():
        if k in file_name:
            result['taxonomy'] = v['taxonomy']
            result['proteome'] = v['proteome']
    return result


@click.group()
def cli():
    """
    tb2neo parses an M.tb GFF file and builds a Neo4j Graph database.
    """
    pass


@cli.command()
def delete():
    """
    Delete existing data.
    :return:
    """
    # Deleting existing data
    delete_db_data()


@cli.command()
@click.argument('gff_files', type=click.Path(exists=True))
def load_organism(gff_files):
    """
    Examine features from GFF file.
    :param gff_files: GFF file directory
    :return
    """
    if os.path.isdir(gff_files):
        for root, dirs, files in os.walk(gff_files):
            for gff_file in files:
                gff_file = '/'.join([os.path.abspath(gff_files), gff_file])
                if gff_file.endswith(".gff3"):
                    click.secho("Examining: {}".format(gff_file), fg="green")
                    create_organism_nodes(gff_file=gff_file)


@cli.command()
@click.argument('strain')
def load_chromosome(strain):
    """
    Load Chromosome for specified strain.
    :param strain: H37RV or CDC1551
    :return:
    """
    supported_strains = ["h37rv", "cdc1551"]

    error_mess = "We currently support {supported}.\nReceived {strain}".format(
        strain=strain, supported=supported_strains)

    if strain and str(strain).lower() in supported_strains:
        if "h37rv" == str(strain).lower():
            strain = "h37rv"
        elif "cdc1551" == str(strain).lower():
            strain = "cdc1551"
        else:
            raise ValueError(error_mess)
        click.echo("Loading {strain} Chromosome...".format(strain=strain))
        create_chromosome_nodes(strain=strain)
    else:
        sys.stderr.write(error_mess)


@cli.command()
@click.argument('gff_files', type=click.Path(exists=True))
def examine_gff(gff_files):
    """
    Examine features from GFF file.
    :param gff_files: GFF file directory
    :return
    """
    if os.path.isdir(gff_files):
        for root, dirs, files in os.walk(gff_files):
            for gff_file in files:
                gff_file = '/'.join([os.path.abspath(gff_files), gff_file])
                if gff_file.endswith(".gff3"):
                    click.secho("Examining: {}".format(gff_file), fg="green")
                    examine_gff_file(gff_file=gff_file)


@cli.command()
@click.argument('gff_files', type=click.Path(exists=True))
def load_gff(gff_files):
    """
    Load GFF features and build relationships.
    :param gff_files:
    :return:
    """
    if os.path.isdir(gff_files):
        for root, dirs, files in os.walk(gff_files):
            for gff_file in files:
                gff_file = '/'.join([os.path.abspath(gff_files), gff_file])
                if gff_file.endswith(".gff3"):
                    click.secho("Loading {}".format(gff_file), fg="green")
                    parse_gff(gff_file)
                    build_gff_relationships()
                    result = get_taxonomy_and_proteome(gff_file)
                    if check_csv(MYCO_GFF) and result['taxonomy'] == '83332':
                        map_functional_category(MYCO_GFF)


@cli.command()
@click.argument('operon_dir', type=click.Path(exists=True))
def load_operons(operon_dir):
    """
    Load Operons.
    :return:
    """
    if os.path.isdir(operon_dir):
        for root, dirs, files in os.walk(operon_dir):
            for _file in files:
                _file = '/'.join([os.path.abspath(operon_dir), _file])
                if check_csv(_file):
                    if _file.endswith(".txt"):
                        create_operon_nodes(text_file=_file)


@cli.command()
@click.argument('mutations', type=click.Path(exists=True))
def load_known_mutations(mutations):
    """
    Load Known Drug Resistant mutations.
    :param mutations:
    :return:
    """
    if os.path.isdir(mutations):
        for root, dirs, files in os.walk(mutations):
            for _file in files:
                _file = '/'.join([os.path.abspath(mutations), _file])
                if check_csv(_file):
                    process_mutation_file(in_file=_file)


@cli.command()
@click.argument('gff_files', type=click.Path(exists=True))
def load_uniprot_data(gff_files):
    """
    Load UniProt data using GFF (locus tags).
    :param gff_files:
    :return:
    """
    if check_csv(UNIPROT_DATA) and not gff_files:
        click.secho("\nLoading UniProt data from csv...", fg="green")
        create_protein_nodes()
    else:
        if os.path.isdir(gff_files):
            for root, dirs, files in os.walk(gff_files):
                click.secho("\nLoading UniProt data from gff...", fg="green")
                for gff_file in files:
                    gff_file = '/'.join([os.path.abspath(gff_files), gff_file])
                    if gff_file.endswith(".gff3"):
                        result = get_taxonomy_and_proteome(gff_file)
                        locus_tags = get_locus_tags(
                            gff_file=gff_file, chunk=400)
                        # TODO: When we have loaded the CDC1551 strain
                        # map_gene_to_orthologs(get_locus_tags(gff_file, 400))
                        query_uniprot(
                            locus_tags=locus_tags, taxonomy=result['taxonomy'],
                            proteome=result['proteome'])
                        # TODO: Need to refactor
                        create_protein_nodes()


@cli.command()
def load_ppi():
    """
    Load Protein-Protein Interactions from STRING-DB.
    :return:
    """
    if check_csv(UNIPROT_DATA):
        load_string_data()
    else:
        sys.stderr.write(
            "Unable to create PPIs!\nCould not find UniProt csv file.")


@cli.command()
def load_drugbank_data():
    """
    Load DrugBank data.
    :return:
    """
    # Let's check if we have Proteins to map to.
    proteins = graph.data("MATCH (p:Protein) RETURN p.entry_name LIMIT 1")
    if len(proteins) > 0 and check_csv(UNIPROT_DATA) \
            and check_csv(TARGET_PROTEIN_IDS) and check_csv(DRUG_VOCAB):
        create_drugbank_nodes()
    else:
        sys.stderr.write("Unable to load Drugbank data!\n.")


@cli.command()
def load_go_terms():
    """
    Load GO terms.
    :return:
    """
    if check_csv(UNIPROT_DATA):
        create_go_term_nodes()
    else:
        sys.stderr.write(
            "Unable to create GOTerms!\nCould not find UniProt csv file.")


@cli.command()
def load_publications():
    """
    Load Publications.
    :return:
    """
    if check_csv(UNIPROT_DATA):
        create_publication_nodes(uniprot_data=UNIPROT_DATA)
    else:
        sys.stderr.write(
            "Unable to load Publications!\nCould not find CSV file.")


@cli.command()
def load_kegg_pathways():
    """
    Load KEGG Pathways.
    :return:
    """
    # Let's check if we have Proteins to map to.
    proteins = graph.data("MATCH (p:Protein) RETURN p.entry_name LIMIT 1")
    if len(proteins) > 0:
        create_kegg_pathways_nodes()
    else:
        sys.stderr.write(
            "Unable to load KEGG Pathways!\nNo Proteins nodes in database.")


@cli.command()
def load_reactome_pathways():
    """
    Load REACTOME Pathways.
    :return:
    """
    # Let's check if we have Proteins to map to.
    proteins = graph.data("MATCH (p:Protein) RETURN p.entry_name LIMIT 1")
    if len(proteins) > 0 and check_csv(UNIPROT_DATA):
        create_reactome_pathway_nodes()
    else:
        sys.stderr.write(
            "Unable to load REACTOME Pathways!\nNo Proteins in database.")


@cli.command()
@click.argument('srna_dir', type=click.Path(exists=True))
def load_srna_data(srna_dir):
    """
    Load regulatory sRNA data.
    :return:
    """
    if os.path.isdir(srna_dir):
        for root, dirs, files in os.walk(srna_dir):
            for _file in files:
                _file = '/'.join([os.path.abspath(srna_dir), _file])
                if check_csv(_file):
                    if _file.endswith(".txt"):
                        map_srna_to_mrna(text_file=_file)


if __name__ == '__main__':
    cli()
