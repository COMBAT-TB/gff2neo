from py2neo.ogm import GraphObject, Property, RelatedTo, RelatedFrom


class Organism(GraphObject):
    """
    Organism
    """
    __primarykey__ = 'genus'

    abbreviation = Property()
    strain = Property()
    genus = Property()
    species = Property()
    common_name = Property()
    comment = Property()

    dbxref = RelatedTo("DbXref", "XREF")

    def __init__(self, abbreviation=None, strain=None, genus=None, species=None, common_name=None, comment=None):
        self.abbreviation = abbreviation
        self.strain = strain
        self.genus = genus
        self.species = species
        self.common_name = common_name
        self.comment = comment


class Feature(GraphObject):
    """
    Used for inheritance purposes
    """
    __primarykey__ = 'uniquename'

    name = Property()
    uniquename = Property()
    residues = Property()
    seqlen = Property()
    md5checksum = Property()
    parent = Property()  # To build related_to rel.
    is_analysis = Property()
    is_obsolete = Property()
    timeaccessioned = Property()
    timelastmodfied = Property()
    ontology_id = Property()

    belongs_to = RelatedTo("Organism", "BELONGS_TO")
    location = RelatedTo("Location", "LOCATED_AT")
    # related_to = RelatedTo("Feature", "RELATED_TO")
    published_in = RelatedTo("Publication", "PUBLISHED_IN")
    dbxref = RelatedTo("DbXref", "XREF")


# class FeatureSet(GraphObject):
#     # I'm not sure if this should be in core - pvh
#     __primarykey__ = 'name'

#     name = Property()
#     description = Property()
#     contains = RelatedTo("Feature", "CONTAINS")


class Gene(Feature):
    """
    Gene is_a Feature
    """
    _so_id = "SO:0000704"
    so_id = Property()
    biotype = Property()
    description = Property()

    # parts = RelatedFrom("Transcript", "PART_OF")
    orthologous_to = RelatedTo("Gene", "ORTHOLOGOUS_TO")

    def __init__(self, so_id=_so_id):
        self.so_id = so_id


class PseudoGene(Feature):
    """
    PseudoGene is_a Feature
    """
    _so_id = "SO:0000336"
    so_id = Property()
    biotype = Property()
    description = Property()

    def __init__(self, so_id=_so_id):
        self.so_id = so_id


class Transcript(Feature):
    """
    Transcript is_a Feature
    """
    _so_id = "SO:0000673"
    so_id = Property()
    biotype = Property()

    part_of = RelatedTo("Gene", "PART_OF")

    def __init__(self, so_id=_so_id):
        self.so_id = so_id


class TRna(Feature):
    """
    TRna is_a Feature
    """
    _so_id = "SO:0000253"
    so_id = Property()

    def __init__(self, so_id=_so_id):
        self.so_id = so_id


class NCRna(Feature):
    """
    NCRna is_a Feature
    """
    _so_id = "SO:0000655"
    so_id = Property()

    def __init__(self, so_id=_so_id):
        self.so_id = so_id


class RRna(Feature):
    """
    RRna is_a Feature
    """
    _so_id = "SO:0000252"
    so_id = Property()

    def __init__(self, so_id=_so_id):
        self.so_id = so_id


class Exon(Feature):
    """
    Exon is_a Feature
    """
    _so_id = "SO:0000147"
    so_id = Property()

    part_of = RelatedTo("Transcript", "PART_OF")

    def __init__(self, so_id=_so_id):
        self.so_id = so_id


class CDS(Feature):
    """
    CDS is_a Feature
    """
    _so_id = "SO:0000316"
    so_id = Property()

    part_of = RelatedTo("Transcript", "PART_OF")

    # protein = RelatedFrom('Protein', "DERIVES_FROM")

    def __init__(self, so_id=_so_id):
        self.so_id = so_id


class Chromosome(Feature):
    """
    Chromosome is_a Feature
    """
    _so_id = "SO:0000340"
    so_id = Property()

    is_a = RelatedTo("Feature", "IS_A")

    def __init__(self, so_id=_so_id):
        self.so_id = so_id


class Protein(Feature):
    """
    Protein is_a Feature
    """
    # more commonly known as a Protein - we should call it that - pvh
    _so_id = "SO:0000104"
    so_id = Property()
    family = Property()
    function = Property()
    pdb_id = Property()
    domain = Property()
    three_d = Property()
    mass = Property()

    derives_from = RelatedTo("CDS", "DERIVES_FROM")
    interacts_with = RelatedTo("Protein", "INTERACTS_WITH")

    def __init__(self, so_id=_so_id):
        self.so_id = so_id


class Location(GraphObject):
    """
    FeatureLoc not used
    """
    __primarykey__ = 'srcfeature_id'  # used feature.uniquename

    srcfeature_id = Property()
    fmin = Property()
    is_fmin_partial = Property()
    fmax = Property()
    is_fmax_partial = Property()
    strand = Property()
    phase = Property()
    residue_info = Property()
    locgroup = Property()
    rank = Property()

    feature = RelatedFrom("Feature", "ON")
    published_in = RelatedTo("Publication", "PUBLISHED_IN")

    def __init__(self, srcfeature_id, fmin=None, is_fmin_partial=None, fmax=None, is_fmax_partial=None, strand=None,
                 phase=None, residue_info=None, locgroup=None,
                 rank=None):
        self.srcfeature_id = srcfeature_id
        self.fmin = fmin
        self.is_fmin_partial = is_fmin_partial
        self.fmax = fmax
        self.is_fmax_partial = is_fmax_partial
        self.strand = strand
        self.phase = phase
        self.residue_info = residue_info
        self.locgroup = locgroup
        self.rank = rank
        if self.fmin > self.fmax:
            raise ValueError(
                "fmin cannot be greater than fmax: {} > {}.".format(self.fmin, self.fmax))


class Publication(GraphObject):
    """
    Publication from PubMed
    """
    __primarykey__ = 'pmid'

    pmid = Property()
    title = Property()
    volumetitle = Property()
    volume = Property()
    series_name = Property()
    issue = Property()
    year = Property()
    pages = Property()
    miniref = Property()
    uniquename = Property()
    is_obsolete = Property()
    publisher = Property()
    pubplace = Property()

    author = RelatedFrom("Author", "WROTE")


class Author(GraphObject):
    """
    Authors
    """
    __primarykey__ = 'givennames'

    editor = Property()
    surname = Property()
    givennames = Property()
    suffix = Property()
    rank = Property()

    wrote = RelatedTo("Publication", "WROTE")

    def __init__(self, editor=None, surname=None, givennames=None, suffix=None):
        self.editor = editor
        self.surname = surname
        self.givennames = givennames
        self.suffix = suffix


class GOTerm(GraphObject):
    """
    Gene Ontology Terms
    """
    __primarykey__ = 'name'

    name = Property()
    definition = Property()
    is_obsolete = Property()
    namespace = Property()

    is_a = RelatedTo("GOTerm", "IS_A")
    # part_of = RelatedTo("GOTerm", "PART_OF")
    # feature = RelatedFrom("Feature", "ASSOC_WITH")

    def __init__(self, name=None, definition=None, is_obsolete=None):
        self.name = name
        self.definition = definition
        self.is_obsolete = is_obsolete


class InterProTerm(GraphObject):
    """
    InterPro Terms
    """
    __primarykey__ = 'name'

    name = Property()
    definition = Property()
    is_obsolete = Property()
    namespace = Property()

    dbxref = RelatedTo("DbXref", "XREF")
    is_a = RelatedTo("GOTerm", "IS_A")
    part_of = RelatedTo("GOTerm", "PART_OF")
    feature = RelatedFrom("Feature", "ASSOC_WITH")

    def __init__(self, name=None, definition=None, is_obsolete=None):
        self.name = name
        self.definition = definition
        self.is_obsolete = is_obsolete


class DbXref(GraphObject):
    """
    External references
    """
    __primarykey__ = 'accession'

    accession = Property()
    version = Property()
    db = Property()
    description = Property()

    def __init__(self, db, accession, version, description=None):
        self.accession = accession
        self.version = version
        self.db = db
        self.description = description


class Contig(GraphObject):
    """
    Contigs
    """
    pass
