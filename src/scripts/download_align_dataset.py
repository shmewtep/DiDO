#! /usr/bin/env python3

import pandas as pd
import csv
import json
import regex
import uuid
import os
import argparse

from datasets import load_dataset

from rdflib import Graph, Literal, RDF, URIRef, Namespace, BNode, XSD, DCTERMS, DC
from rdflib.namespace import RDFS

DATA_DIRECTORY = os.path.join('src', 'ontology', 'data')

# 1. Define Namespaces based on DIDO.ttl
DIDO = Namespace("http://purl.org/twc/dido#")
SIO = Namespace("http://semanticscience.org/resource/")
PROV = Namespace("http://www.w3.org/ns/prov#")
TIME = Namespace("http://www.w3.org/2006/time#")
EX = Namespace("http://purl.org/twc/dido/individuals#")
DCAT = Namespace("http://www.w3.org/ns/dcat#")


def align_ami_jsonl_to_dido(jsonl_file, n_utterances=None):
    '''
    Transform data points from AMI JSONL format to RDF format, aligned with DIDO.
    '''
    g = Graph()
    
    # Bind namespaces
    g.bind("dido", DIDO)
    g.bind("sio", SIO)
    g.bind("time", TIME)
    g.bind("dcat", DCAT)
    g.bind("ex", EX)

    meeting_id = os.path.basename(jsonl_file).split('.')[0]

    # --- Dialogue Structure ---
    dialogue_uri = EX[f"dialogue{meeting_id}"]
    g.add((dialogue_uri, RDF.type, DIDO.Dialogue))

    # --- Metadata (DialogueTranscript & Dataset) ---
    transcript_uri = EX[f"dialogueTranscript{meeting_id}"]
    g.add((transcript_uri, RDF.type, DIDO.DialogueTranscript))
    g.add((transcript_uri, SIO.SIO_000332, dialogue_uri)) # sio:is about

    ami_dataset_uri = EX["dataset_ami"]
    g.add((ami_dataset_uri, RDF.type, SIO.SIO_000089)) # sio:dataset
    g.add((ami_dataset_uri, RDF.type, DCAT.Dataset))
    g.add((transcript_uri, SIO.SIO_000095, ami_dataset_uri)) # sio:is member of
    g.add((transcript_uri, DCTERMS.title, Literal("AMI Meeting Corpus", datatype=XSD.string)))
    g.add((ami_dataset_uri, DCAT.landingPage, URIRef('https://groups.inf.ed.ac.uk/ami/corpus/')))
    g.add((ami_dataset_uri, DCTERMS.isReferencedBy, URIRef('https://doi.org/10.1007/11677482_3')))


    with open(jsonl_file, 'r') as f:
        for utterance_num, line in enumerate(f):
            if n_utterances is not None and utterance_num >= n_utterances:
                break

            data = json.loads(line)
            
            # --- Dialogue Structure ---
            utterance_id = f"{meeting_id}{utterance_num}"
            utterance_uri = EX[f"utterance{utterance_id}"]
            g.add((utterance_uri, RDF.type, DIDO.Utterance))
            
            # Linking Utterance to the Dialogue
            g.add((utterance_uri, SIO.SIO_000068, dialogue_uri)) # sio:is part of
            
            # --- DIDO-core: Participant (SIO Agent) ---
            interlocutor_uri = EX[f"human{data['speaker_id']}"]
            interlocutor_role_uri = EX[f"interlocutor{data['speaker_id']}"]
            
            g.add((interlocutor_uri, RDF.type, SIO.SIO_000485)) # sio:human
            g.add((interlocutor_uri, SIO.SIO_000062, dialogue_uri)) # sio:is participant in
            g.add((interlocutor_uri, SIO.SIO_000063, utterance_uri))  # sio:is agent in
            g.add((interlocutor_uri, SIO.SIO_000228, interlocutor_role_uri)) # sio:has role
            
            g.add((utterance_uri, SIO.SIO_000139, interlocutor_uri))  # sio:has agent
            
            g.add((interlocutor_role_uri, RDF.type, DIDO.Interlocutor))
            g.add((interlocutor_role_uri, SIO.SIO_000227, interlocutor_uri)) # sio:is role of
            g.add((interlocutor_role_uri, SIO.SIO_000356, dialogue_uri)) # sio:is realized in

            g.add((dialogue_uri, SIO.SIO_000132, interlocutor_uri)) # sio:has participant
            g.add((dialogue_uri, SIO.SIO_000355, interlocutor_role_uri)) # sio:realizes

            # --- DIDO-data: Transcript (SIO Entity) ---
            utterance_text_uri = EX[f"utteranceText{utterance_id}"]
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

        dialogue_uri = EX[f"dialogue_{dialogue_num}"]
        g.add((dialogue_uri, RDF.type, DIDO.Dialogue))

        # Transcript/Dataset metadata
        transcript_uri = EX[f"dialogueTranscript_{dialogue_num}"]
        g.add((transcript_uri, RDF.type, DIDO.DialogueTranscript))
        g.add((transcript_uri, SIO.SIO_000332, dialogue_uri)) # sio:is about

        daic_woz_uri = EX[f"dataset_daic-woz"]
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
            utterance_uri = EX[f"utterance_{utterance_id}"]
            g.add((utterance_uri, RDF.type, DIDO.Utterance))

            # Linking Utterance to the Dialogue
            g.add((utterance_uri, SIO.SIO_000068, dialogue_uri)) # sio:is part of

            # --- DIDO-core: Participant (SIO Agent) ---
            interlocutor_uri = ''
            interlocutor_role_uri = ''
            if utterance['speaker'] == 'Ellie':
                interlocutor_uri = EX[f"human_ellie"]
                interlocutor_role_uri = EX[f"interlocutor_ellie"]
            else:
                interlocutor_uri = EX[f"human_{dialogue_num}"]
                interlocutor_role_uri = EX[f"interlocutor_{dialogue_num}"]

            g.add((interlocutor_uri, RDF.type, SIO.SIO_000485)) # sio:human
            g.add((interlocutor_uri, SIO.SIO_000062, dialogue_uri)) # sio:is participant in
            g.add((interlocutor_uri, SIO.SIO_000063, utterance_uri))  # sio:is agent in
            g.add((interlocutor_uri, SIO.SIO_000228, interlocutor_role_uri)) # sio:has role
            
            g.add((utterance_uri, SIO.SIO_000139, interlocutor_uri))  # sio:has agent
            
            g.add((interlocutor_role_uri, RDF.type, DIDO.Interlocutor))
            g.add((interlocutor_role_uri, SIO.SIO_000227, interlocutor_uri)) # sio:is role of
            g.add((interlocutor_role_uri, SIO.SIO_000356, dialogue_uri)) # sio:is realized in

            g.add((dialogue_uri, SIO.SIO_000132, interlocutor_uri)) # sio:has participant
            g.add((dialogue_uri, SIO.SIO_000355, interlocutor_role_uri)) # sio:realizes

            # --- DIDO-data: Transcript (SIO Entity) ---
            utterance_text_uri = EX[f"utteranceText_{utterance_id}"]
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


def get_first_n_dialogues(dataset, n=None):
    """Collect the first `n` distinct dialogues (meetings) from `dataset`.

    Iterates over `dataset` (an iterable of example dicts or a streaming
    dataset) and groups examples by the `meeting_id` field. Stops once `n`
    distinct meeting IDs have been collected. If `n` is None, collects all.
    Returns a list of `pandas.DataFrame` objects, one per collected meeting, 
    preserving the encounter order.

    Parameters:
    - dataset: iterable of mapping-like examples (each must contain
        a `meeting_id` key).
    - n (int, optional): number of distinct meetings to collect.

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
            if n is not None and len(meeting_order) >= n:
                # If data is contiguous, we can 'break' here to save time.
                break
            
            meeting_order.append(meeting_id)
            meeting_groups[meeting_id] = []
        
        # Append the instance data (converted to a dictionary) to the correct group
        # Using vars(item) assumes the instance attributes match your desired columns
        meeting_groups[meeting_id].append(item)

    # Convert each collected list of dictionaries into a DataFrame
    return [pd.DataFrame(meeting_groups[m_id]) for m_id in meeting_order]


def get_target_dialogues(dataset, target_ids):
    """Collect specific distinct dialogues (meetings) from `dataset`.

    Iterates over `dataset` and groups examples by the `meeting_id` field.
    Stops once all requested meeting IDs have been collected.

    Parameters:
    - dataset: iterable of mapping-like examples.
    - target_ids (list of str): specific meeting IDs to collect.

    Returns:
    - List[pandas.DataFrame]: list of DataFrames, one per meeting collected.
    """
    meeting_groups = {}
    meeting_order = []
    target_ids_set = set(target_ids)

    for item in dataset:
        meeting_id = item['meeting_id']
        
        if meeting_id in target_ids_set:
            if meeting_id not in meeting_groups:
                meeting_order.append(meeting_id)
                meeting_groups[meeting_id] = []
            
            meeting_groups[meeting_id].append(item)
        elif len(meeting_order) == len(target_ids_set):
            # If data is contiguous and we've collected all requested IDs, we can break.
            break

    return [pd.DataFrame(meeting_groups[m_id]) for m_id in meeting_order]


def save_individual_dialogues_as_json(dialogues, output_dir=DATA_DIRECTORY):
    """Save each dialogue DataFrame as an individual JSON file."""
    os.makedirs(os.path.join(output_dir, 'dialog_ami'), exist_ok=True)
    
    for dialogue in dialogues:
        output_path = os.path.join(output_dir, 'dialog_ami', f"{dialogue.iloc[0]['meeting_id']}.jsonl")
        print(f"Saving dialogue {dialogue.iloc[0]['meeting_id']} to {output_path}...")
        dialogue.to_json(output_path, orient="records", lines=True)




def download_dataset(num_conversations=None, dialogue_id=None):

    """Download and prepare a small slice of a configured corpus.

    Currently configured to download the AMI Meeting Corpus via
    `datasets.load_dataset` with streaming enabled. The function removes
    unwanted audio columns and returns a list of DataFrames containing 
    either the requested dialogue IDs, the first `num_conversations` meetings,
    or all meetings if neither is provided.

    Parameters:
    - num_conversations (int, optional): number of meetings to download and return (if dialogue_id is not set).
    - dialogue_id (str or List[str], optional): specific dialogue ID(s) to download.

    Returns:
    - List[pandas.DataFrame]: list of dialogues as DataFrames.
    """

    # Define specific settings for each corpus
    corpus_configs = {
        "AMI Meeting Corpus": {
            "path": "edinburghcstr/ami",
            "name": "ihm",          # AMI requires a subset name (e.g., 'ihm' or 'sdm')
            "streaming": True,
            "split": "train"
        },
    }
    
    # Download corpus from HuggingFace
    corpus_name = "AMI Meeting Corpus"
    corpus_config = corpus_configs[corpus_name]

    print(f"Downloading {corpus_name} with settings: {corpus_config}")
    dataset = load_dataset(**corpus_config)
    
    # Remove audio columns to prevent datasets from attempting to decode it
    dataset = dataset.remove_columns(['audio_id', 'audio']) 

    if dialogue_id is not None:
        if isinstance(dialogue_id, str):
            dialogue_id = [dialogue_id]
        dialogues = get_target_dialogues(dataset, dialogue_id)
    else:
        dialogues = get_first_n_dialogues(dataset, num_conversations)

    return dialogues


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Align dialogue dataset to DIDO ontology.")
    parser.add_argument("--dataset", type=str, required=True, choices=["ami", "daicwoz"], help="Dataset name (ami or daicwoz)")
    parser.add_argument("--dialogue_id", type=str, nargs="+", help="Dialogue ID(s) (e.g., EN2001a or 301). Can provide multiple.")
    parser.add_argument("--n", type=int, help="Number of dialogues to download/align (starting from the first).")
    parser.add_argument("--dialogue_location", type=str, help="Location of the dialogue transcript file (JSONL or CSV). Required if not using --download.")
    parser.add_argument("--output_dir", type=str, default=os.path.join('..', '..', 'src', 'ontology', 'data'), help="Output directory for the RDF file")
    parser.add_argument("--download", action="store_true", help="Download the dialogue from HuggingFace first (currently only supports AMI)")
    
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    if args.download:
        if args.dataset != "ami":
            raise ValueError("Downloading is currently only supported for the AMI dataset.")
        print("Downloading dataset...")
        dialogues = download_dataset(num_conversations=args.n, dialogue_id=args.dialogue_id)
        save_individual_dialogues_as_json(dialogues, output_dir=args.output_dir)
        
        for dialogue in dialogues:
            d_id = dialogue.iloc[0]['meeting_id']
            loc = os.path.join(args.output_dir, 'dialog_ami', f"{d_id}.jsonl")
            rdf_dest = os.path.join(args.output_dir, f'dialog_{args.dataset}', f'ami_meeting_{d_id}.ttl')
            print(f"Aligning AMI meeting {d_id} from {loc}...")
            g_ami = align_ami_jsonl_to_dido(loc)
            print(f"Writing to {rdf_dest}")
            g_ami.serialize(destination=rdf_dest, format='turtle')
            print(f"\nDone!")

    else:
        if not args.dialogue_location:
            parser.error("--dialogue_location is required when --download is not set")
            
        d_ids = args.dialogue_id
        if not d_ids:
            # Infer from filename
            base = os.path.basename(args.dialogue_location)
            base_no_ext = os.path.splitext(base)[0]
            inferred_id = base_no_ext.replace('_TRANSCRIPT', '')
            d_ids = [inferred_id]
            
        for d_id in d_ids:
            if args.dataset == "daicwoz":
                rdf_dest = os.path.join(args.output_dir, f'daicwoz_dialogue_{d_id}.ttl')
                print(f"Aligning DAIC-WOZ dialogue {d_id} from {args.dialogue_location}...")
                g_daic_woz = align_daicwoz_csv_to_dido(args.dialogue_location)
                print(f"Writing to {rdf_dest}")
                g_daic_woz.serialize(destination=rdf_dest, format='turtle')
                print(f"\nDone!")

            elif args.dataset == "ami":
                rdf_dest = os.path.join(args.output_dir, f'ami_meeting_{d_id}.ttl')
                print(f"Aligning AMI meeting {d_id} from {args.dialogue_location}...")
                g_ami = align_ami_jsonl_to_dido(args.dialogue_location, n_utterances=50)
                print(f"Writing to {rdf_dest}")
                g_ami.serialize(destination=rdf_dest, format='turtle')
                print(f"\nDone!")