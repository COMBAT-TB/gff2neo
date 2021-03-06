"""
Variant Processing
"""
import re
import sys

from Bio.SeqUtils import seq1
from bioservices import KEGG
from pandas import read_csv
from tqdm import tqdm
from tb2neo.dbconn import create_known_mutation_nodes

kegg = KEGG(verbose=False)

drug_groups = ["aminoglycosides", "fluoroquinolones"]


def get_drug_info(drug_name):
    """
    Get Drug Info
    :param drug_name:
    :return:
    """
    drugbank_id, drug_info = None, dict()
    if 'aminosalicylic_acid' in drug_name:
        drug_name = 'Aminosalicylic acid'
    if drug_name not in drug_groups:
        k_drug = kegg.find("drug", str(drug_name))
        drug_id = k_drug.split('\t')[0]
        drug_info = kegg.parse(kegg.get(drug_id))
        if not isinstance(drug_info, int):
            dblinks = drug_info.get("DBLINKS")
            if dblinks:
                drugbank_id = dblinks.get("DrugBank")
    return drugbank_id


def _process_coll_mutations(in_file, cset_name):
    """
    Load Coll et al. mutation Library
    :param in_file:
    :param cset_name:
    :return:
    """
    sys.stdout.write("\nProcessing {cset}...\n".format(cset=cset_name))
    drugbank_id, biotype = None, ''
    vset_name = "Coll"
    vset_owner = "Coll, F. et al."
    for line in in_file:
        if not line.startswith("#"):

            tab_split = line.strip().split('\t')
            drug_name = tab_split[9].lower()
            drugbank_id = get_drug_info(drug_name)

            variant_pos = tab_split[1]
            # gi|444893469|emb|AL123456.3|	1674484/1674485	inhA	Rv1484	283/284	95	A/T/C/C	ATT/CCT	I/P	ISONIAZID	MUBII-TB-DB
            # check base pair length
            # ref_allele, alt_allele = "", ""
            bps = tab_split[6]
            bp_mid = len(bps.split("/")) / 2
            bps = bps.replace("/", "")
            ref_allele = bps[:int(bp_mid)]
            alt_allele = bps[int(bp_mid):]

            # amino acid change
            gene_cord = tab_split[4]
            codon_number = tab_split[5]
            amino_change = tab_split[8].strip().split("/")
            if len(amino_change) > 1 and amino_change[0] == amino_change[1]:
                biotype = 'synonymous'
            elif len(amino_change) > 1 and amino_change[0] is not \
                    amino_change[1]:
                biotype = 'non-synonymous'
            elif len(ref_allele) is not len(alt_allele):
                biotype = "indel"

            # ['Leu', 'Pro'] to ['Leu', 123,'Pro']
            amino_change.insert(1, codon_number)
            # ['Leu', 123, 'Pro'] to 'Leu123Pro'
            consequence = ''.join(amino_change) if biotype != "indel" \
                else ref_allele + gene_cord + alt_allele
            # some string manipulation kung-fu
            # '(Jnawali_et_al.,_2013)' => 'Jnawali_et_al.,_2013'
            table = str.maketrans(dict.fromkeys('()'))
            sources = tab_split[10].translate(table)

            if "_promoter" in tab_split[2]:
                promoter = tab_split[2]
                gene_name = tab_split[2].split("_")[0]
                consequence = ref_allele + gene_cord + alt_allele
                biotype = 'promoter'
            else:
                gene_name = tab_split[2]
                promoter = None

            create_known_mutation_nodes(chrom="Chr1", pos=variant_pos,
                                        ref_allele=str(ref_allele),
                                        alt_allele=str(alt_allele),
                                        gene=gene_name,
                                        promoter=promoter,
                                        pk=str(drug_name + consequence
                                               + variant_pos + ref_allele
                                               + alt_allele).lower(),
                                        consequence=consequence,
                                        vset_name=vset_name,
                                        vset_owner=vset_owner,
                                        cset_name=cset_name, sources=sources,
                                        drugbank_id=drugbank_id,
                                        drug_name=drug_name, biotype=biotype)


def _process_tbprofiler_mutations(in_file, cset_name):
    """
    Load TBProfiler mutation Library
    :param in_file:
    :param cset_name:
    :return:
    """
    sys.stdout.write(f"\nProcessing {cset_name}...\n")
    drugbank_id, biotype, drugbank_dict, promoter = None, '', dict(), ''
    vset_name = "TBProfiler"
    vset_owner = "https://github.com/jodyphelan"
    for line in tqdm(in_file):
        if not line.startswith("#"):
            drugbank_ids = set()
            tab_split = line.split('\t')
            drug_name = tab_split[0].lower()

            variant_pos = tab_split[1]
            variant_pos = variant_pos.split(
                '/')[0] if '/' in variant_pos else variant_pos

            ref_allele = tab_split[2]
            alt_allele = tab_split[3]
            if "_promoter" in tab_split[4]:
                promoter = tab_split[4]
                gene_name = tab_split[4].split("_")[0]
                biotype = "promoter"
            else:
                gene_name = tab_split[4]
                promoter = None
            # amino acid change
            consequence = tab_split[5].strip()
            # Pro241Pro to ['Pro', '241', 'Pro']
            amino_change = re.split(r"(\d+)", consequence)
            # consequence = [seq1(a, custom_map={"*": "Stop"}, undef_code='-')
            #                for a in amino_change if not a.isdigit()]
            # consequence.insert(1, amino_change[1])
            # consequence = ''.join(consequence)

            if amino_change[0] == amino_change[2]:
                biotype = "synonymous"
            elif amino_change[0] is not amino_change[2]:
                biotype = "non-synonymous"
            elif len(ref_allele) is not len(alt_allele) \
                    and '-' not in consequence:
                biotype = "indel"

            if drug_name not in drugbank_dict.values() and drug_groups:
                drugbank_id = get_drug_info(drug_name)
                if drugbank_id:
                    drugbank_dict[drugbank_id] = drug_name
                    drugbank_ids.add(drugbank_id)
            else:
                for drug_id, name in drugbank_dict.items():
                    if drug_name == name:
                        drugbank_id = drug_id
                        drugbank_ids.add(drugbank_id)

            create_known_mutation_nodes(chrom="Chr1", pos=variant_pos,
                                        ref_allele=str(ref_allele),
                                        alt_allele=str(alt_allele),
                                        gene=gene_name,
                                        promoter=promoter,
                                        pk=str(drug_name + consequence
                                               + variant_pos + ref_allele
                                               + alt_allele).lower(),
                                        consequence=consequence,
                                        vset_name=vset_name,
                                        vset_owner=vset_owner,
                                        cset_name=cset_name,
                                        drugbank_id=drugbank_ids,
                                        drug_name=drug_name, biotype=biotype)


def _process_tbprofiler_two_mutations(in_file, cset_name):
    """
    Load TBProfiler mutation Library
    :param in_file:
    :param cset_name:
    :return:
    """
    sys.stdout.write(f"\nProcessing {cset_name}...\n")
    drugbank_id, biotype, drugbank_dict, promoter = None, '', dict(), ''
    vset_name = "TBDB"
    vset_owner = "https://github.com/jodyphelan"
    df = read_csv(in_file).fillna("")
    for entry in tqdm(df.values):
        drugbank_ids = set()
        gene_name = entry[0]
        consequence = entry[1]
        amino_change = consequence
        variant_pos = consequence
        ref_allele = alt_allele = consequence
        if '.' in consequence:
            consequence_split = consequence.split('.')
            # Pro241Pro to ['Pro', '241', 'Pro']
            amino_change = re.split(r"(\d+)", consequence_split[1])
            variant_pos = amino_change[1]
            if '>' in consequence:
                ref_allele = amino_change[2].split('>')[0].upper()
                alt_allele = amino_change[2].split('>')[1].upper()
            else:
                ref_allele = amino_change[0]
                alt_allele = amino_change[2]

        drug_name = entry[2]
        if drug_name not in drugbank_dict.values() and drug_groups:
            drugbank_id = get_drug_info(drug_name)
            if drugbank_id:
                drugbank_dict[drugbank_id] = drug_name
                drugbank_ids.add(drugbank_id)
        else:
            for drug_id, name in drugbank_dict.items():
                if drug_name == name:
                    drugbank_id = drug_id
                    drugbank_ids.add(drugbank_id)

        create_known_mutation_nodes(chrom="Chr1", pos=variant_pos,
                                    ref_allele=str(ref_allele),
                                    alt_allele=str(alt_allele),
                                    gene=gene_name,
                                    promoter=promoter,
                                    pk=str(drug_name + consequence
                                           + variant_pos + ref_allele
                                           + alt_allele).lower(),
                                    consequence=consequence,
                                    vset_name=vset_name,
                                    vset_owner=vset_owner,
                                    cset_name=cset_name,
                                    drugbank_id=drugbank_ids,
                                    drug_name=drug_name, biotype=biotype)


def _process_phyresse_mutations(in_file, cset_name):
    """
    Load PhyResSe mutation Library
    :param in_file:
    :param cset_name:
    :return:
    """
    sys.stdout.write(f"\nProcessing {cset_name}...\n")
    biotype, drugbank_dict, promoter = '', dict(), ''
    vset_name = "PhyResSe"
    vset_owner = "Feuerriegel S, Schleusener V, Beckert P, et al."
    df = read_csv(in_file).fillna("")
    for entry in tqdm(df.values):
        drugbank_ids = set()
        gene_name = entry[5]
        consequence = entry[7]
        amino_change = entry[0]
        variant_pos = str(entry[0])
        ref_allele = entry[1]
        alt_allele = entry[2]
        # TODO: 1473246,A,G,ribosomal,MTB000019,rrs,+,---,-,
        # "amikacin, kanamycin, capreomycin",High confidence
        drug = entry[9].replace(" ", "")
        drugs = drug.split(',') if ',' in drug else drug.split()
        for drug_name in drugs:
            if drug_name not in drugbank_dict.values() and drug_groups:
                drugbank_id = get_drug_info(drug_name)
                if drugbank_id:
                    drugbank_dict[drugbank_id] = drug_name
                    drugbank_ids.add(drugbank_id)
            else:
                for drug_id, name in drugbank_dict.items():
                    if drug_name == name:
                        drugbank_id = drug_id
                        drugbank_ids.add(drugbank_id)

        create_known_mutation_nodes(chrom="Chr1", pos=variant_pos,
                                    ref_allele=str(ref_allele),
                                    alt_allele=str(alt_allele),
                                    gene=gene_name,
                                    promoter=promoter,
                                    pk=str(drug + consequence
                                           + variant_pos + ref_allele
                                           + alt_allele).lower(),
                                    consequence=consequence,
                                    vset_name=vset_name,
                                    vset_owner=vset_owner,
                                    cset_name=cset_name,
                                    drugbank_id=drugbank_ids,
                                    drug_name=drug, biotype=biotype)


def process_mutation_file(in_file):
    """
    Process mutation file
    :param in_file:
    :return:
    """

    if in_file:
        if in_file.endswith(".txt"):
            with open(in_file) as in_file:
                next(in_file)
                cset_name = str(in_file.name).split('/')[-1]
                if 'coll' in cset_name:
                    pass
                    # _process_coll_mutations(
                    #     in_file=in_file, cset_name=cset_name)
                elif 'drdb' in cset_name:
                    # pass
                    _process_tbprofiler_mutations(in_file=in_file,
                                                  cset_name=cset_name)
        else:
            cset_name = in_file.split('/')[-1]
            if 'phyresse' in cset_name:
                # pass
                _process_phyresse_mutations(in_file, cset_name)
            if 'tbdb' in cset_name:
                pass
                # _process_tbprofiler_two_mutations(in_file, cset_name)
