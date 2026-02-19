import pandas as pd
import csv
import json
import regex
import uuid
import os

from rdflib import Graph, Literal, RDF, URIRef, Namespace, BNode, XSD, DCTERMS, DC
from rdflib.namespace import RDFS


# 1. Define Namespaces based on DIDO.ttl
DIDO = Namespace("http://purl.org/twc/dido#")
SIO = Namespace("http://semanticscience.org/resource/")
PROV = Namespace("http://www.w3.org/ns/prov#")
TIME = Namespace("http://www.w3.org/2006/time#")
EX = Namespace("http://purl.org/twc/dido/individuals#")
DCAT = Namespace("http://www.w3.org/ns/dcat#")


def align_ami_jsonl_to_dido(jsonl_file):
    '''
    Transform data points from AMI JSONL format to RDF format, aligned with DIDO.
    '''
    g = Graph()
    
    # Bind namespaces
    g.bind("dido", DIDO)
    g.bind("sio", SIO)
    g.bind("time", TIME)
    g.bind("dcat", DCAT)

    meeting_id = os.path.basename(jsonl_file).split('.')[0]

    # --- Dialogue Structure ---
    dialogue_uri = EX[f"dialogue/{meeting_id}"]
    g.add((dialogue_uri, RDF.type, DIDO.Dialogue))

    # --- Metadata (DialogueTranscript & Dataset) ---
    transcript_uri = EX[f"dialogueTranscript/{meeting_id}"]
    g.add((transcript_uri, RDF.type, DIDO.DialogueTranscript))
    g.add((transcript_uri, SIO.SIO_000332, dialogue_uri)) # sio:is about

    ami_dataset_uri = EX["dataset/ami"]
    g.add((ami_dataset_uri, RDF.type, SIO.SIO_000089)) # sio:dataset
    g.add((ami_dataset_uri, RDF.type, DCAT.Dataset))
    g.add((transcript_uri, SIO.SIO_000095, ami_dataset_uri)) # sio:is member of
    g.add((transcript_uri, DCTERMS.title, Literal("AMI Meeting Corpus", datatype=XSD.string)))
    g.add((ami_dataset_uri, DCAT.landingPage, URIRef('https://groups.inf.ed.ac.uk/ami/corpus/')))
    g.add((ami_dataset_uri, DCTERMS.isReferencedBy, URIRef('https://doi.org/10.1007/11677482_3')))


    with open(jsonl_file, 'r') as f:
        for utterance_num, line in enumerate(f):
            data = json.loads(line)
            
            # --- Dialogue Structure ---
            utterance_id = f"{meeting_id}_{utterance_num}"
            utterance_uri = EX[f"utterances/utterance_{utterance_id}"]
            g.add((utterance_uri, RDF.type, DIDO.Utterance))
            
            # Linking Utterance to the Dialogue
            g.add((utterance_uri, SIO.SIO_000068, dialogue_uri)) # sio:is part of
            
            # --- DIDO-core: Participant (SIO Agent) ---
            participant_uri = EX[f"interlocutors/{data['speaker_id']}"]
            g.add((participant_uri, RDF.type, DIDO.Interlocutor))
            g.add((participant_uri, SIO.SIO_000062, dialogue_uri)) # sio:is participant in
            g.add((utterance_uri, SIO.SIO_000139, participant_uri))  # sio:has agent
            g.add((participant_uri, SIO.SIO_000063, utterance_uri))  # sio:is agent in

            # --- DIDO-data: Transcript (SIO Entity) ---
            utterance_text_uri = EX[f"utteranceTexts/utteranceText_{utterance_id}"]
            g.add((utterance_text_uri, RDF.type, DIDO.UtteranceText))
            g.add((utterance_uri, SIO.SIO_000232, utterance_text_uri))  # sio:has output
            g.add((utterance_text_uri, SIO.SIO_000300, Literal(data['text'], datatype=XSD.string)))   # sio:has value
            
            # --- Temporal duration (OWL-Time) ---
            g.add((utterance_uri, RDF.type, TIME.TemporalEntity))
            temporal_duration_node = BNode()
            g.add((utterance_uri, SIO.sio_000008, temporal_duration_node))    # sio:has attribute

            beg_node = BNode()
            end_node = BNode()
            g.add((beg_node, RDF.type, TIME.Instant))
            g.add((end_node, RDF.type, TIME.Instant))
            g.add((temporal_duration_node, TIME.hasBeginning, beg_node))
            g.add((temporal_duration_node, TIME.hasEnd, end_node))

            # --- Temporal instant descriptions (OWL-TIME) ---
            beg_node_description = BNode()
            end_node_description = BNode()
            g.add((beg_node_description, RDF.type, TIME.DateTimeDescription))
            g.add((end_node_description, RDF.type, TIME.DateTimeDescription))
            g.add((beg_node, TIME.inDateTime, beg_node_description))
            g.add((end_node, TIME.inDateTime, end_node_description))
            g.add((beg_node_description, TIME.second, Literal(data['begin_time'], datatype=XSD.float)))
            g.add((end_node_description, TIME.second, Literal(data['end_time'], datatype=XSD.float)))
            g.add((beg_node_description, TIME.unitType, TIME.unitSecond))
            g.add((end_node_description, TIME.unitType, TIME.unitSecond))

    return g


def align_daicwoz_csv_to_dido(csv_filename):
    '''
    Transform data points from DAIC-WOZ CSV format to RDF format, aligned with DIDO.
    '''
    g = Graph()
    
    # Bind namespaces
    g.bind("dido", DIDO)
    g.bind("sio", SIO)
    g.bind("time", TIME)
    g.bind("dcat", DCAT)

    dialogue_num_pattern = regex.compile(r"^.*(\d{3})_TRANSCRIPT\.csv$")
    dialogue_num = dialogue_num_pattern.match(csv_filename).group(1)

    with open(csv_filename) as csv_file:
        reader = csv.DictReader(csv_file, delimiter='\t')

        dialogue_uri = EX[f"dialogue/{dialogue_num}"]
        g.add((dialogue_uri, RDF.type, DIDO.Dialogue))

        # Transcript/Dataset metadata
        transcript_uri = EX[f"dialogueTranscript/{dialogue_num}"]
        g.add((transcript_uri, RDF.type, DIDO.DialogueTranscript))
        g.add((transcript_uri, SIO.SIO_000332, dialogue_uri)) # sio:is about

        daic_woz_uri = EX[f"dataset/daic-woz"]
        g.add((daic_woz_uri, RDF.type, SIO.SIO_000089)) # sio:dataset
        g.add((daic_woz_uri, RDF.type, DCAT.Dataset))
        g.add((transcript_uri, SIO.SIO_000095, daic_woz_uri)) # sio:is member of\
        g.add((transcript_uri, DCTERMS.title, Literal("Distress Analysis Corpus - Wizard of Oz", datatype=XSD.string)))
        g.add((daic_woz_uri, DCAT.landingPage, URIRef('https://dcapswoz.ict.usc.edu/')))
        g.add((daic_woz_uri, DCTERMS.isReferencedBy, URIRef('https://d1wqtxts1xzle7.cloudfront.net/98764174/508_Paper-libre.pdf')))

        for utterance_num, utterance in enumerate(reader):
            # print(utterance)
            # --- Dialogue Structure ---
            # Using meeting_id as the primary identifier for the Dialogue instance
            utterance_id = f"{dialogue_num}_{utterance_num}"
            utterance_uri = EX[f"utterances/utterance_{utterance_id}"]
            g.add((utterance_uri, RDF.type, DIDO.Utterance))

            # Linking Utterance to the Dialogue
            g.add((utterance_uri, SIO.SIO_000068, dialogue_uri)) # sio:is part of

            # --- DIDO-core: Participant (SIO Agent) ---
            participant_uri = ''
            if utterance['speaker'] == 'Ellie':
                participant_uri = EX[f"interlocutors/{'ellie'}"]
            else:
                participant_uri = EX[f"interlocutors/interlocutor_{dialogue_num}"]

            g.add((participant_uri, RDF.type, DIDO.Interlocutor))
            g.add((participant_uri, SIO.SIO_000062, dialogue_uri)) # sio:is participant in
            g.add((utterance_uri, SIO.SIO_000139, participant_uri))  # sio:has agent
            g.add((participant_uri, SIO.SIO_000063, utterance_uri))  # sio:is agent in

            # --- DIDO-data: Transcript (SIO Entity) ---
            utterance_text_uri = EX[f"utteranceTexts/utteranceText_{utterance_id}"]
            g.add((utterance_text_uri, RDF.type, DIDO.UtteranceText))
            g.add((utterance_uri, SIO.SIO_000232, utterance_text_uri))  # sio:has output
            g.add((utterance_text_uri, SIO.SIO_000300, Literal(utterance['value'], datatype=XSD.string)))   # sio:has value
            
            # --- Temporal duration (OWL-Time) ---
            g.add((utterance_uri, RDF.type, TIME.TemporalEntity))
            temporal_duration_node = BNode()
            g.add((utterance_uri, SIO.sio_000008, temporal_duration_node))    # sio:has attribute

            beg_node = BNode()
            end_node = BNode()
            g.add((beg_node, RDF.type, TIME.Instant))
            g.add((end_node, RDF.type, TIME.Instant))
            g.add((temporal_duration_node, TIME.hasBeginning, beg_node))
            g.add((temporal_duration_node, TIME.hasEnd, end_node))

            # --- Temporal instant descriptions (OWL-TIME) ---
            beg_node_description = BNode()
            end_node_description = BNode()
            g.add((beg_node_description, RDF.type, TIME.DateTimeDescription))
            g.add((end_node_description, RDF.type, TIME.DateTimeDescription))
            g.add((beg_node, TIME.inDateTime, beg_node_description))
            g.add((end_node, TIME.inDateTime, end_node_description))
            g.add((beg_node_description, TIME.second, Literal(utterance['start_time'], datatype=XSD.float)))
            g.add((end_node_description, TIME.second, Literal(utterance['stop_time'], datatype=XSD.float)))
            g.add((beg_node_description, TIME.unitType, TIME.unitSecond))
            g.add((end_node_description, TIME.unitType, TIME.unitSecond))

    return g


def get_first_n_dialogues(dataset, n):
    """Collect the first `n` distinct dialogues (meetings) from `dataset`.

    Iterates over `dataset` (an iterable of example dicts or a streaming
    dataset) and groups examples by the `meeting_id` field. Stops once `n`
    distinct meeting IDs have been collected. Returns a list of
    `pandas.DataFrame` objects, one per collected meeting, preserving the
    encounter order.

    Parameters:
    - dataset: iterable of mapping-like examples (each must contain
        a `meeting_id` key).
    - n (int): number of distinct meetings to collect.

    Returns:
    - List[pandas.DataFrame]: list of DataFrames, one per meeting collected.
    """
    meeting_groups = {}
    meeting_order = []

    for item in dataset:
        # print(item)
        meeting_id = item['meeting_id']
        
        # Check if we've encountered this meeting ID before
        if meeting_id not in meeting_groups:
            # If we already have n meetings, stop collecting new ones
            if len(meeting_order) >= n:
                # If data is contiguous, we can 'break' here to save time.
                break
            
            meeting_order.append(meeting_id)
            meeting_groups[meeting_id] = []
        
        # Append the instance data (converted to a dictionary) to the correct group
        # Using vars(item) assumes the instance attributes match your desired columns
        meeting_groups[meeting_id].append(item)

    # Convert each collected list of dictionaries into a DataFrame
    return [pd.DataFrame(meeting_groups[m_id]) for m_id in meeting_order]



if __name__ == "__main__":
    # DAIC-WOZ Alignment
    dialogue_num_daicwoz = 300
    csv_filename_daicwoz = os.path.join('src', 'ontology', 'data', 'dialog_daicwoz', f'{dialogue_num_daicwoz}_TRANSCRIPT.csv')
    rdf_dest_daicwoz = os.path.join('src', 'ontology', 'data', f'daicwoz_dialogue_{dialogue_num_daicwoz}.ttl')
    
    print(f"Aligning DAIC-WOZ dialogue {dialogue_num_daicwoz}...")
    g_daic_woz = align_daicwoz_csv_to_dido(csv_filename_daicwoz)
    # print(f"Writing to {rdf_dest_daicwoz}")
    # g_daic_woz.serialize(destination=rdf_dest_daicwoz, format='turtle')

    # AMI Alignment
    meeting_id_ami = 'EN2001a'
    jsonl_filename_ami = os.path.join('src', 'ontology', 'data', 'dialog_ami', f'{meeting_id_ami}.jsonl')
    rdf_dest_ami = os.path.join('src', 'ontology', 'data', f'ami_meeting_{meeting_id_ami}.ttl')

    print(f"Aligning AMI meeting {meeting_id_ami}...")
    g_ami = align_ami_jsonl_to_dido(jsonl_filename_ami)
    print(f"Writing to {rdf_dest_ami}")
    g_ami.serialize(destination=rdf_dest_ami, format='turtle')