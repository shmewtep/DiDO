#! /usr/bin/env python3

import pandas as pd
import csv
import json
import regex
import uuid
import os
import argparse

from datasets import load_dataset
import datasets

from rdflib import Graph, Literal, RDF, URIRef, Namespace, BNode, XSD, DCTERMS, DC
from rdflib.namespace import RDFS

DATA_DIRECTORY = os.path.join('src', 'ontology', 'data')

# 1. Define Namespaces based on DIDO.ttl
DIDO = Namespace("http://purl.org/dido#")
SIO = Namespace("http://semanticscience.org/resource/")
PROV = Namespace("http://www.w3.org/ns/prov#")
TIME = Namespace("http://www.w3.org/2006/time#")
EX = Namespace("http://purl.org/twc/dido/individuals#")
DCAT = Namespace("http://www.w3.org/ns/dcat#")
POWLA = Namespace("http://purl.org/powla/powla.owl#")


def _add_temporal_bounds(g, entity_uri, begin_time, end_time):
    g.add((entity_uri, RDF.type, TIME.TemporalEntity))
    temporal_duration_node = BNode()
    g.add((entity_uri, SIO.sio_000008, temporal_duration_node))    # sio:has attribute

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
    g.add((beg_node_description, TIME.second, Literal(begin_time, datatype=XSD.float)))
    g.add((end_node_description, TIME.second, Literal(end_time, datatype=XSD.float)))
    g.add((beg_node_description, TIME.unitType, TIME.unitSecond))
    g.add((end_node_description, TIME.unitType, TIME.unitSecond))


def align_ami_jsonl_to_dido(jsonl_file, n_utterances=None):
    g = Graph()
    g.bind("dido", DIDO)
    g.bind("sio", SIO)
    g.bind("time", TIME)
    g.bind("dcat", DCAT)
    g.bind("ex", EX)
    g.bind("powla", POWLA)

    meeting_id = os.path.basename(jsonl_file).split('.')[0]

    dialogue_uri = EX[f"dialogue{meeting_id}"]
    g.add((dialogue_uri, RDF.type, DIDO.Dialogue))

    transcript_uri = EX[f"dialogueTranscript{meeting_id}"]
    g.add((transcript_uri, RDF.type, DIDO.DialogueTranscript))
    g.add((transcript_uri, SIO.SIO_000332, dialogue_uri))

    ami_dataset_uri = EX["dataset_ami"]
    g.add((ami_dataset_uri, RDF.type, SIO.SIO_000089))
    g.add((ami_dataset_uri, RDF.type, DCAT.Dataset))
    g.add((transcript_uri, SIO.SIO_000095, ami_dataset_uri))
    g.add((transcript_uri, DCTERMS.title, Literal("AMI Meeting Corpus", datatype=XSD.string)))
    g.add((ami_dataset_uri, DCAT.landingPage, URIRef('https://groups.inf.ed.ac.uk/ami/corpus/')))
    g.add((ami_dataset_uri, DCTERMS.isReferencedBy, URIRef('https://doi.org/10.1007/11677482_3')))

    utterances = []
    with open(jsonl_file, 'r') as f:
        for utterance_num, line in enumerate(f):
            if n_utterances is not None and utterance_num >= n_utterances:
                break
            utterances.append(json.loads(line))

    turns = []
    if utterances:
        current_turn = {
            'speaker_id': utterances[0]['speaker_id'],
            'begin_time': utterances[0]['begin_time'],
            'end_time': utterances[0]['end_time'],
            'utterances': [utterances[0]],
            'turn_num': 0
        }
        for data in utterances[1:]:
            if data['speaker_id'] == current_turn['speaker_id']:
                current_turn['end_time'] = data['end_time']
                current_turn['utterances'].append(data)
            else:
                turns.append(current_turn)
                current_turn = {
                    'speaker_id': data['speaker_id'],
                    'begin_time': data['begin_time'],
                    'end_time': data['end_time'],
                    'utterances': [data],
                    'turn_num': len(turns)
                }
        turns.append(current_turn)

    global_utt_num = 0
    for turn in turns:
        turn_id = f"{meeting_id}{turn['turn_num']}"
        turn_uri = EX[f"turn{turn_id}"]
        g.add((turn_uri, RDF.type, DIDO.Turn))
        g.add((turn_uri, SIO.SIO_000068, dialogue_uri))
        
        turn_text_uri = EX[f"turnText{turn_id}"]
        g.add((turn_text_uri, RDF.type, DIDO.TurnText))
        g.add((turn_uri, SIO.SIO_000229, turn_text_uri))
        concatenated_text = " ".join([u['text'] for u in turn['utterances']])
        g.add((turn_text_uri, SIO.SIO_000300, Literal(concatenated_text, datatype=XSD.string)))

        _add_temporal_bounds(g, turn_uri, turn['begin_time'], turn['end_time'])

        interlocutor_uri = EX[f"human{turn['speaker_id']}"]
        interlocutor_role_uri = EX[f"interlocutor{turn['speaker_id']}"]
        
        g.add((interlocutor_uri, RDF.type, SIO.SIO_000485))
        g.add((interlocutor_uri, SIO.SIO_000062, dialogue_uri))
        g.add((interlocutor_uri, SIO.SIO_000228, interlocutor_role_uri))
        g.add((interlocutor_role_uri, RDF.type, DIDO.Interlocutor))
        g.add((interlocutor_role_uri, SIO.SIO_000227, interlocutor_uri))
        g.add((interlocutor_role_uri, SIO.SIO_000356, dialogue_uri))
        g.add((dialogue_uri, SIO.SIO_000132, interlocutor_uri))
        g.add((dialogue_uri, SIO.SIO_000355, interlocutor_role_uri))

        g.add((interlocutor_uri, SIO.SIO_000063, turn_uri))
        g.add((turn_uri, SIO.SIO_000139, interlocutor_uri))

        for data in turn['utterances']:
            utterance_id = f"{meeting_id}{global_utt_num}"
            utterance_uri = EX[f"utterance{utterance_id}"]
            g.add((utterance_uri, RDF.type, DIDO.Utterance))
            g.add((utterance_uri, SIO.SIO_000068, turn_uri)) 

            g.add((interlocutor_uri, SIO.SIO_000063, utterance_uri))
            g.add((utterance_uri, SIO.SIO_000139, interlocutor_uri))
            
            utterance_text_uri = EX[f"utteranceText{utterance_id}"]
            g.add((utterance_text_uri, RDF.type, DIDO.UtteranceText))
            g.add((utterance_uri, SIO.SIO_000229, utterance_text_uri))
            g.add((utterance_text_uri, SIO.SIO_000300, Literal(data['text'], datatype=XSD.string)))
            
            g.add((utterance_uri, RDF.type, POWLA.Nonterminal))
            if 'da_type' in data and data['da_type']:
                da_annotation_uri = EX[f"daAnnotation{utterance_id}"]
                dialogue_act_uri = EX[f"dialogueAct{utterance_id}"]
                g.add((utterance_uri, SIO.SIO_000292, da_annotation_uri))
                g.add((utterance_uri, SIO.SIO_000225, dialogue_act_uri))
                g.add((da_annotation_uri, RDF.type, DIDO.DialogueActAnnotation))
                g.add((da_annotation_uri, RDF.type, POWLA.Terminal))
                g.add((da_annotation_uri, SIO.SIO_000332, dialogue_act_uri))
                g.add((da_annotation_uri, SIO.SIO_000291, utterance_uri))
                g.add((da_annotation_uri, SIO.SIO_000300, Literal(data['da_type'], datatype=XSD.string)))
                g.add((dialogue_act_uri, RDF.type, DIDO.DialogueAct))
                da_class_name = data['da_type'].replace(' ', '').replace('-', '')
                if da_class_name:
                    g.add((dialogue_act_uri, RDF.type, DIDO[da_class_name]))
                g.add((dialogue_act_uri, SIO.SIO_000226, utterance_uri))

            _add_temporal_bounds(g, utterance_uri, data['begin_time'], data['end_time'])
            global_utt_num += 1

    return g


def align_daicwoz_csv_to_dido(csv_filename):
    g = Graph()
    g.bind("dido", DIDO)
    g.bind("sio", SIO)
    g.bind("time", TIME)
    g.bind("dcat", DCAT)
    g.bind("powla", POWLA)

    dialogue_num_pattern = regex.compile(r"^.*(\d{3})_TRANSCRIPT\.csv$")
    dialogue_num = dialogue_num_pattern.match(csv_filename).group(1)

    with open(csv_filename) as csv_file:
        reader = list(csv.DictReader(csv_file, delimiter='\t'))

        dialogue_uri = EX[f"dialogue_{dialogue_num}"]
        g.add((dialogue_uri, RDF.type, DIDO.Dialogue))

        transcript_uri = EX[f"dialogueTranscript_{dialogue_num}"]
        g.add((transcript_uri, RDF.type, DIDO.DialogueTranscript))
        g.add((transcript_uri, SIO.SIO_000332, dialogue_uri))

        daic_woz_uri = EX[f"dataset_daic-woz"]
        g.add((daic_woz_uri, RDF.type, SIO.SIO_000089))
        g.add((daic_woz_uri, RDF.type, DCAT.Dataset))
        g.add((transcript_uri, SIO.SIO_000095, daic_woz_uri))
        g.add((transcript_uri, DCTERMS.title, Literal("Distress Analysis Corpus - Wizard of Oz", datatype=XSD.string)))
        g.add((daic_woz_uri, DCAT.landingPage, URIRef('https://dcapswoz.ict.usc.edu/')))
        g.add((daic_woz_uri, DCTERMS.isReferencedBy, URIRef('https://d1wqtxts1xzle7.cloudfront.net/98764174/508_Paper-libre.pdf')))

        turns = []
        if reader:
            current_turn = {
                'speaker_id': reader[0]['speaker'],
                'begin_time': float(reader[0]['start_time']),
                'end_time': float(reader[0]['stop_time']),
                'utterances': [reader[0]],
                'turn_num': 0
            }
            for data in reader[1:]:
                if data['speaker'] == current_turn['speaker_id']:
                    current_turn['end_time'] = float(data['stop_time'])
                    current_turn['utterances'].append(data)
                else:
                    turns.append(current_turn)
                    current_turn = {
                        'speaker_id': data['speaker'],
                        'begin_time': float(data['start_time']),
                        'end_time': float(data['stop_time']),
                        'utterances': [data],
                        'turn_num': len(turns)
                    }
            turns.append(current_turn)

        global_utt_num = 0
        for turn in turns:
            turn_id = f"{dialogue_num}_{turn['turn_num']}"
            turn_uri = EX[f"turn_{turn_id}"]
            g.add((turn_uri, RDF.type, DIDO.Turn))
            g.add((turn_uri, SIO.SIO_000068, dialogue_uri))
            
            turn_text_uri = EX[f"turnText_{turn_id}"]
            g.add((turn_text_uri, RDF.type, DIDO.TurnText))
            g.add((turn_uri, SIO.SIO_000229, turn_text_uri))
            concatenated_text = " ".join([u['value'] for u in turn['utterances']])
            g.add((turn_text_uri, SIO.SIO_000300, Literal(concatenated_text, datatype=XSD.string)))

            _add_temporal_bounds(g, turn_uri, turn['begin_time'], turn['end_time'])

            if turn['speaker_id'] == 'Ellie':
                interlocutor_uri = EX[f"human_ellie"]
                interlocutor_role_uri = EX[f"interlocutor_ellie"]
            else:
                interlocutor_uri = EX[f"human_{dialogue_num}"]
                interlocutor_role_uri = EX[f"interlocutor_{dialogue_num}"]
                
            g.add((interlocutor_uri, RDF.type, SIO.SIO_000485))
            g.add((interlocutor_uri, SIO.SIO_000062, dialogue_uri))
            g.add((interlocutor_uri, SIO.SIO_000228, interlocutor_role_uri))
            g.add((interlocutor_role_uri, RDF.type, DIDO.Interlocutor))
            g.add((interlocutor_role_uri, SIO.SIO_000227, interlocutor_uri))
            g.add((interlocutor_role_uri, SIO.SIO_000356, dialogue_uri))
            g.add((dialogue_uri, SIO.SIO_000132, interlocutor_uri))
            g.add((dialogue_uri, SIO.SIO_000355, interlocutor_role_uri))

            g.add((interlocutor_uri, SIO.SIO_000063, turn_uri))
            g.add((turn_uri, SIO.SIO_000139, interlocutor_uri))

            for data in turn['utterances']:
                utterance_id = f"{dialogue_num}_{global_utt_num}"
                utterance_uri = EX[f"utterance_{utterance_id}"]
                g.add((utterance_uri, RDF.type, DIDO.Utterance))
                g.add((utterance_uri, RDF.type, POWLA.Nonterminal))
                g.add((utterance_uri, SIO.SIO_000068, turn_uri))

                g.add((interlocutor_uri, SIO.SIO_000063, utterance_uri))
                g.add((utterance_uri, SIO.SIO_000139, interlocutor_uri))
                
                utterance_text_uri = EX[f"utteranceText_{utterance_id}"]
                g.add((utterance_text_uri, RDF.type, DIDO.UtteranceText))
                g.add((utterance_uri, SIO.SIO_000229, utterance_text_uri))
                g.add((utterance_text_uri, SIO.SIO_000300, Literal(data['value'], datatype=XSD.string)))

                _add_temporal_bounds(g, utterance_uri, float(data['start_time']), float(data['stop_time']))
                global_utt_num += 1

    return g


def align_dailydialog_to_dido(dialogue_id, dialogue_data):
    g = Graph()
    g.bind("dido", DIDO)
    g.bind("sio", SIO)
    g.bind("dcat", DCAT)
    g.bind("ex", EX)
    g.bind("powla", POWLA)

    dialogue_uri = EX[f"dialogue_dd_{dialogue_id}"]
    g.add((dialogue_uri, RDF.type, DIDO.Dialogue))

    transcript_uri = EX[f"dialogueTranscript_dd_{dialogue_id}"]
    g.add((transcript_uri, RDF.type, DIDO.DialogueTranscript))
    g.add((transcript_uri, SIO.SIO_000332, dialogue_uri))

    dd_dataset_uri = EX["dataset_dailydialog"]
    g.add((dd_dataset_uri, RDF.type, SIO.SIO_000089))
    g.add((dd_dataset_uri, RDF.type, DCAT.Dataset))
    g.add((transcript_uri, SIO.SIO_000095, dd_dataset_uri))
    g.add((transcript_uri, DCTERMS.title, Literal("DailyDialog Corpus", datatype=XSD.string)))
    g.add((dd_dataset_uri, DCAT.landingPage, URIRef('https://huggingface.co/datasets/daily_dialog')))
    g.add((dd_dataset_uri, DCTERMS.isReferencedBy, URIRef('https://arxiv.org/abs/1710.03957')))

    speaker_a_uri = EX[f"human_dd_{dialogue_id}_A"]
    speaker_b_uri = EX[f"human_dd_{dialogue_id}_B"]
    role_a_uri = EX[f"interlocutor_dd_{dialogue_id}_A"]
    role_b_uri = EX[f"interlocutor_dd_{dialogue_id}_B"]

    for speaker_uri, role_uri in [(speaker_a_uri, role_a_uri), (speaker_b_uri, role_b_uri)]:
        g.add((speaker_uri, RDF.type, SIO.SIO_000485))
        g.add((speaker_uri, SIO.SIO_000062, dialogue_uri))
        g.add((speaker_uri, SIO.SIO_000228, role_uri))
        g.add((role_uri, RDF.type, DIDO.Interlocutor))
        g.add((role_uri, SIO.SIO_000227, speaker_uri))
        g.add((role_uri, SIO.SIO_000356, dialogue_uri))
        g.add((dialogue_uri, SIO.SIO_000132, speaker_uri))
        g.add((dialogue_uri, SIO.SIO_000355, role_uri))

    act_mapping = {
        1: "Inform",
        2: "Question",
        3: "Directive",
        4: "Commissive"
    }

    # DailyDialog turns perfectly alternate speaker A and B each utterance in the HF dataset!
    # "The DailyDialog dataset contains multi-turn dialogues where speakers alternate."
    # We can consider each utterance as a turn directly since they are already alternating.
    
    for turn_idx, (text, act_id) in enumerate(zip(dialogue_data['utterances'], dialogue_data['acts'])):
        turn_id = f"dd_{dialogue_id}_{turn_idx}"
        turn_uri = EX[f"turn_{turn_id}"]
        g.add((turn_uri, RDF.type, DIDO.Turn))
        g.add((turn_uri, SIO.SIO_000068, dialogue_uri))
        
        speaker_uri = speaker_a_uri if turn_idx % 2 == 0 else speaker_b_uri
        g.add((speaker_uri, SIO.SIO_000063, turn_uri))
        g.add((turn_uri, SIO.SIO_000139, speaker_uri))
        
        turn_text_uri = EX[f"turnText_{turn_id}"]
        g.add((turn_text_uri, RDF.type, DIDO.TurnText))
        g.add((turn_uri, SIO.SIO_000229, turn_text_uri))
        g.add((turn_text_uri, SIO.SIO_000300, Literal(text, datatype=XSD.string)))

        # Utterance
        utterance_id = turn_id
        utterance_uri = EX[f"utterance_{utterance_id}"]
        g.add((utterance_uri, RDF.type, DIDO.Utterance))
        g.add((utterance_uri, RDF.type, POWLA.Nonterminal))
        g.add((utterance_uri, SIO.SIO_000068, turn_uri))

        g.add((speaker_uri, SIO.SIO_000063, utterance_uri))
        g.add((utterance_uri, SIO.SIO_000139, speaker_uri))

        utterance_text_uri = EX[f"utteranceText_{utterance_id}"]
        g.add((utterance_text_uri, RDF.type, DIDO.UtteranceText))
        g.add((utterance_uri, SIO.SIO_000229, utterance_text_uri))
        g.add((utterance_text_uri, SIO.SIO_000300, Literal(text, datatype=XSD.string)))

        da_type = act_mapping.get(act_id, "DialogueAct")
        da_annotation_uri = EX[f"daAnnotation_{utterance_id}"]
        dialogue_act_uri = EX[f"dialogueAct_{utterance_id}"]

        g.add((utterance_uri, SIO.SIO_000292, da_annotation_uri))
        g.add((utterance_uri, SIO.SIO_000225, dialogue_act_uri))

        g.add((da_annotation_uri, RDF.type, DIDO.DialogueActAnnotation))
        g.add((da_annotation_uri, RDF.type, POWLA.Terminal))
        g.add((da_annotation_uri, SIO.SIO_000332, dialogue_act_uri))
        g.add((da_annotation_uri, SIO.SIO_000291, utterance_uri))
        g.add((da_annotation_uri, SIO.SIO_000300, Literal(da_type, datatype=XSD.string)))

        g.add((dialogue_act_uri, RDF.type, DIDO.DialogueAct))
        g.add((dialogue_act_uri, RDF.type, DIDO[da_type]))
        g.add((dialogue_act_uri, SIO.SIO_000226, utterance_uri))

    return g


def get_first_n_dialogues(dataset, n=None):
    meeting_groups = {}
    meeting_order = []
    for item in dataset:
        meeting_id = item['meeting_id']
        if meeting_id not in meeting_groups:
            if n is not None and len(meeting_order) >= n:
                break
            meeting_order.append(meeting_id)
            meeting_groups[meeting_id] = []
        meeting_groups[meeting_id].append(item)
    return [pd.DataFrame(meeting_groups[m_id]) for m_id in meeting_order]


def get_target_dialogues(dataset, target_ids):
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
            break
    return [pd.DataFrame(meeting_groups[m_id]) for m_id in meeting_order]


def save_individual_dialogues_as_json(dialogues, output_dir=DATA_DIRECTORY):
    os.makedirs(os.path.join(output_dir, 'dialog_ami'), exist_ok=True)
    for dialogue in dialogues:
        output_path = os.path.join(output_dir, 'dialog_ami', f"{dialogue.iloc[0]['meeting_id']}.jsonl")
        print(f"Saving dialogue {dialogue.iloc[0]['meeting_id']} to {output_path}...")
        dialogue.to_json(output_path, orient="records", lines=True)


def download_dataset(num_conversations=None, dialogue_id=None):
    corpus_configs = {
        "AMI Meeting Corpus": {
            "path": "edinburghcstr/ami",
            "name": "ihm",
            "streaming": True,
            "split": "train"
        },
    }
    corpus_name = "AMI Meeting Corpus"
    corpus_config = corpus_configs[corpus_name]
    print(f"Downloading {corpus_name} with settings: {corpus_config}")
    dataset = load_dataset(**corpus_config)
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
    parser.add_argument("--dataset", type=str, required=True, choices=["ami", "daicwoz", "dailydialog"], help="Dataset name")
    parser.add_argument("--dialogue_id", type=str, nargs="+", help="Dialogue ID(s)")
    parser.add_argument("--n", type=int, help="Number of dialogues to download/align")
    parser.add_argument("--dialogue_location", type=str, help="Location of the dialogue transcript file")
    parser.add_argument("--output_dir", type=str, default=os.path.join('..', '..', 'src', 'ontology', 'data'), help="Output directory")
    parser.add_argument("--download", action="store_true", help="Download from HuggingFace first")
    
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    if args.download:
        if args.dataset not in ["ami", "dailydialog"]:
            raise ValueError("Downloading only supported for AMI and DailyDialog.")
        
        if args.dataset == "ami":
            print("Downloading dataset...")
            dialogues = download_dataset(num_conversations=args.n, dialogue_id=args.dialogue_id)
            save_individual_dialogues_as_json(dialogues, output_dir=args.output_dir)
            
            for dialogue in dialogues:
                d_id = dialogue.iloc[0]['meeting_id']
                loc = os.path.join(args.output_dir, 'dialog_ami', f"{d_id}.jsonl")
                rdf_dest = os.path.join(args.output_dir, f'dialog_{args.dataset}', f'ami_meeting_{d_id}.ttl')
                os.makedirs(os.path.dirname(rdf_dest), exist_ok=True)
                print(f"Aligning AMI meeting {d_id} from {loc}...")
                g_ami = align_ami_jsonl_to_dido(loc)
                print(f"Writing to {rdf_dest}")
                g_ami.serialize(destination=rdf_dest, format='turtle')
                print(f"\nDone!")
                
        elif args.dataset == "dailydialog":
            print("Downloading DailyDialog dataset...")
            from datasets import load_dataset
            dataset = load_dataset('roskoN/dailydialog', split='train')
            n_dialogues = args.n if args.n is not None else 3
            os.makedirs(os.path.join(args.output_dir, 'dialog_dailydialog'), exist_ok=True)
            for idx, dialogue_data in enumerate(dataset):
                if idx >= n_dialogues:
                    break
                d_id = str(idx)
                rdf_dest = os.path.join(args.output_dir, 'dialog_dailydialog', f'dailydialog_dialogue_{d_id}.ttl')
                print(f"Aligning DailyDialog dialogue {d_id}...")
                g_dd = align_dailydialog_to_dido(d_id, dialogue_data)
                print(f"Writing to {rdf_dest}")
                g_dd.serialize(destination=rdf_dest, format='turtle')
                print(f"\nDone!")
    else:
        if not args.dialogue_location:
            parser.error("--dialogue_location is required when --download is not set")
        d_ids = args.dialogue_id
        if not d_ids:
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
