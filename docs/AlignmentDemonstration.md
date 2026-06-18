---
title: Alignment Demonstration
layout: single
sidebar:
        nav: "docs"
---

# Dialogue Corpora Semantic Alignment Demonstration

This page demonstrates how the **Discourse and Dialogue Ontology (DIDO)** semantically aligns dialogue datasets of completely different formats, structures, and schemas, allowing them to be queried uniformly via SPARQL.

---

## 1. Aligned Dialogue Corpora

We compare two highly distinct dialogue corpora:

1. **AMI Meeting Corpus**
   * **Source Format**: JSONL files (one utterance per row).
   * **Structure**: Multi-party face-to-face meetings (3-4 participants).
   * **Annotations**: Precise start/stop timestamps, speaker identifiers, and a detailed dialogue act taxonomy (e.g., *Stall*, *Assess*, *Elicit-Inform*).
2. **DailyDialog Corpus**
   * **Source Format**: Hugging Face dataset features (entire conversation per row with lists for utterances and acts).
   * **Structure**: Alternating two-party casual text chats.
   * **Annotations**: Implicit turn sequences (no timestamps) and 4 standardized speech act categories (*Inform*, *Question*, *Directive*, *Commissive*).

---

## 2. DIDO Mapping Schema

Both corpora are mapped to a unified set of classes and relations:

| Concept / Element | DIDO / SIO Ontology Class or Property | AMI Mapping | DailyDialog Mapping |
| :--- | :--- | :--- | :--- |
| **Dialogue Session** | `dido:Dialogue` | Merged meeting session (`ex:dialogueES2002a`) | Individual conversation (`ex:dialogue_dd_0`) |
| **Utterance** | `dido:Utterance` | Individual speaker segments (`ex:utteranceES2002a0`) | Individual text turns (`ex:utterance_dd_0_0`) |
| **Turn** | `dido:Turn` | Individual speaker turns (`ex:turnES2002a0`) | Individual text turns (`ex:utterance_dd_0_0`) |
| **Transcript Content** | `dido:UtteranceText` | Transcribed speech value (`sio:SIO_000300`) | Text utterance value (`sio:SIO_000300`) |
| **Participant** | `dido:Interlocutor` | Meeting participants (`ex:humanC`, `ex:humanB`, etc.) | Alternating speakers (`ex:human_dd_0_A`, `ex:human_dd_0_B`) |
| **Dialogue Act** | `dido:DialogueAct` | Custom subclass classes (e.g., `dido:Stall`, `dido:Offer`) | Standard speech acts (e.g., `dido:Directive`, `dido:Question`) |
| **Metadata** | `dido:DialogueTranscript` | Dataset descriptor (`dcat:Dataset`) with LDC metadata | Dataset descriptor (`dcat:Dataset`) with HF metadata |

> [!NOTE]
> **Turns vs. Utterances**:
> As defined in DiDO, a **Turn** is a continuous period of speech by one speaker (which can contain multiple sentences), while an **Utterance** is a single functional unit serving some function(s) within a dialogue. While the definitions of Turn and Utterance vary across the literature and are sometimes conflated with each other, we choose this particular terminology to refer to these concepts within DiDO.
> - **AMI** distinguishes between them: a single speaker turn can contain multiple short utterances, each with its own dialogue act.
> - **DailyDialog** conflates them: the entire speaker turn (which may contain multiple sentences) is annotated with a single dialogue act, making Turn and Utterance 1-to-1 in its dataset representation.
> We map each annotated unit in DailyDialog to both `dido:Utterance` and its implicit `dido:Turn`.

---

## 3. SPARQL Queries

To demonstrate semantic interoperability, a Python script (`src/scripts/run_alignment_demo.py`) merges the aligned Turtle files from both datasets into a single RDF graph and executes SPARQL queries across them.

### Query 1: Identify Dialogues and Dataset Provenance
This query retrieves all dialogue instances, their parent dataset titles, and landing pages:

```sparql
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
```

### Query 2: Dialogue Metrics (Utterance & Speaker Counts)
This query calculates basic structural metrics (number of utterances and distinct speakers) for dialogues from both corpora:

```sparql
PREFIX dido: <http://purl.org/dido#>
PREFIX sio: <http://semanticscience.org/resource/>

SELECT ?dialogue (COUNT(DISTINCT ?utterance) AS ?utteranceCount) (COUNT(DISTINCT ?speaker) AS ?speakerCount) WHERE {
  ?utterance a dido:Utterance ;
             sio:SIO_000068 ?dialogue ; # sio:is part of
             sio:SIO_000139 ?speaker .  # sio:has agent
} GROUP BY ?dialogue
```

### Query 3: Dialogue Act Distributions
This query breaks down the occurrences of different dialogue act (speech act) types:

```sparql
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
```

---

## 4. How to Run the Demo

To re-run the download, alignment, and joint query demo from scratch:

1. **Install Dependencies**:
   ```bash
   pip install -r src/scripts/requirements.txt
   ```
2. **Download & Align DailyDialog**:
   ```bash
   python src/scripts/download_align_dataset.py --dataset dailydialog --download --n 3 --output_dir src/ontology/data
   ```
3. **Download & Align AMI**:
   ```bash
   python src/scripts/download_align_dataset.py --dataset ami --dialogue_id ES2002a --download --output_dir src/ontology/data
   ```
4. **Execute Joint Query Demo**:
   ```bash
   python src/scripts/run_alignment_demo.py
   ```

