#!/usr/bin/env python3

import os
from rdflib import Graph

def main():
    # 1. Initialize merged graph
    merged_graph = Graph()

    # Define paths
    data_dir = os.path.join('src', 'ontology', 'data')
    ami_file = os.path.join(data_dir, 'dialog_ami', 'ami_meeting_ES2002a.ttl')
    dd_dir = os.path.join(data_dir, 'dialog_dailydialog')

    print("======================================================================")
    print("DIDO Dialogue Corpora Alignment Demo")
    print("======================================================================")
    print("Note on terminological alignment (Turns vs. Utterances):")
    print(" - In dialogue theory, a Turn is a continuous block of speech by one speaker,")
    print("   while an Utterance is a single unit with a dialogue act.")
    print(" - In AMI, a single speaker Turn can contain multiple short Utterances, each")
    print("   with its own distinct dialogue act.")
    print(" - In DailyDialog, entire speaker Turns (which may contain multiple sentences)")
    print("   are annotated with a single dialogue act, making Turn and Utterance 1-to-1.")
    print(" DIDO maps both structures uniformly to DIDO classes.")
    print("======================================================================\n")

    # 2. Load AMI aligned RDF data
    if os.path.exists(ami_file):
        print(f"Loading AMI aligned dataset from: {ami_file}...")
        merged_graph.parse(ami_file, format='turtle')
        print(f"Loaded AMI graph (Current total triples: {len(merged_graph)})")
    else:
        print(f"[WARNING] AMI aligned file not found at {ami_file}")

    # 3. Load DailyDialog aligned RDF data
    if os.path.exists(dd_dir):
        print(f"Loading DailyDialog aligned files from: {dd_dir}...")
        for filename in os.listdir(dd_dir):
            if filename.endswith('.ttl'):
                filepath = os.path.join(dd_dir, filename)
                print(f" - Loading {filename}...")
                merged_graph.parse(filepath, format='turtle')
        print(f"Loaded DailyDialog graphs (Current total triples: {len(merged_graph)})")
    else:
        print(f"[WARNING] DailyDialog aligned folder not found at {dd_dir}")

    if len(merged_graph) == 0:
        print("Error: Merged graph is empty. Please run the alignment script first.")
        return

    print("\n----------------------------------------------------------------------")
    print("Query 1: Identify Dialogues and Dataset Provenance")
    print("----------------------------------------------------------------------")
    query_1 = """
    PREFIX dido: <http://purl.org/dido#>
    PREFIX sio: <http://semanticscience.org/resource/>
    PREFIX dcterms: <http://purl.org/dc/terms/>
    PREFIX dcat: <http://www.w3.org/ns/dcat#>

    SELECT ?dialogue ?datasetTitle ?landingPage WHERE {
      ?transcript a dido:DialogueTranscript ;
                  dcterms:title ?datasetTitle ;
                  sio:SIO_000332 ?dialogue ;   # sio:is about
                  sio:SIO_000095 ?dataset .    # sio:is member of
      ?dataset a dcat:Dataset ;
               dcat:landingPage ?landingPage .
    }
    """
    results_1 = merged_graph.query(query_1)
    print(f"{'Dialogue URI':<55} | {'Dataset Source':<20} | {'Landing Page'}")
    print("-" * 110)
    for row in results_1:
        dialogue_local = str(row.dialogue).replace("http://purl.org/twc/dido/individuals#", "ex:")
        print(f"{dialogue_local:<55} | {str(row.datasetTitle):<20} | {str(row.landingPage)}")

    print("\n----------------------------------------------------------------------")
    print("Query 2: Dialogue Metrics (Utterance & Speaker Counts)")
    print("----------------------------------------------------------------------")
    query_2 = """
    PREFIX dido: <http://purl.org/dido#>
    PREFIX sio: <http://semanticscience.org/resource/>

    SELECT ?dialogue (COUNT(DISTINCT ?utterance) AS ?utteranceCount) (COUNT(DISTINCT ?speaker) AS ?speakerCount) WHERE {
      ?utterance a dido:Utterance ;
                 sio:SIO_000068 ?dialogue ; # sio:is part of
                 sio:SIO_000139 ?speaker .  # sio:has agent
    } GROUP BY ?dialogue
    """
    results_2 = merged_graph.query(query_2)
    print(f"{'Dialogue':<55} | {'Utterances':<10} | {'Speakers'}")
    print("-" * 80)
    for row in results_2:
        dialogue_local = str(row.dialogue).replace("http://purl.org/twc/dido/individuals#", "ex:")
        print(f"{dialogue_local:<55} | {int(row.utteranceCount):<10} | {int(row.speakerCount)}")

    print("\n----------------------------------------------------------------------")
    print("Query 3: Dialogue Act Distributions")
    print("----------------------------------------------------------------------")
    query_3 = """
    PREFIX dido: <http://purl.org/dido#>
    PREFIX sio: <http://semanticscience.org/resource/>

    SELECT ?dialogue ?actType (COUNT(?da) AS ?actCount) WHERE {
      ?utterance a dido:Utterance ;
                 sio:SIO_000068 ?dialogue ;
                 sio:SIO_000225 ?da .      # sio:has function
      ?da a dido:DialogueAct ;
          a ?type .
      FILTER(?type != dido:DialogueAct && STRSTARTS(STR(?type), "http://purl.org/dido#"))
      BIND(REPLACE(STR(?type), "http://purl.org/dido#", "") AS ?actType)
    } GROUP BY ?dialogue ?actType
    ORDER BY ?dialogue DESC(?actCount)
    """
    results_3 = merged_graph.query(query_3)
    print(f"{'Dialogue':<55} | {'Dialogue Act (Speech Act)':<25} | {'Occurrences'}")
    print("-" * 95)
    for row in results_3:
        dialogue_local = str(row.dialogue).replace("http://purl.org/twc/dido/individuals#", "ex:")
        print(f"{dialogue_local:<55} | {str(row.actType):<25} | {int(row.actCount)}")

    print("\n======================================================================")
    print("Dialogue alignment querying demo completed.")
    print("======================================================================")

if __name__ == '__main__':
    main()
