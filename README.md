# dialogueOnt



## Repository Structure

- [Requirements.md](Requirements.md): Ontology requirements including goals, scope, and target audience.
- [CompetencyQuestions.md](CompetencyQuestions.md): Functional requirements expressed as competency questions.
- [Terms.md](Terms.md): List of terms, prefixes, and definitions used in the ontology.
- [DevelopmentDescription.md](DevelopmentDescription.md): Overview of the ontology development process and methodology.
- `src/`: Contains core ontology files (`ontology/`), scripts (`scripts/`), and SPARQL queries (`sparql/`).
- `docs/`: Contains the web application logic, UI elements, and related queries/data for https://shmewtep.github.io/dialogueOnt/.

## Usage

### Aligning Dialogue Datasets

The `src/scripts/download_align_dataset.py` script can be used to convert dialogue transcripts from the AMI or DAIC-WOZ datasets into RDF format aligned with the DIDO ontology.

**For the AMI dataset:**

You can download the dataset directly from HuggingFace and align it by using the `--download` flag. The transcript file will be automatically saved to `src/ontology/data/dialog_ami/`.

To download a specific dialogue:
```bash
python src/scripts/download_align_dataset.py --dataset ami --dialogue_id EN2001a --download
```

To download and align multiple specific dialogues at once:
```bash
python src/scripts/download_align_dataset.py --dataset ami --dialogue_id EN2001a ES2002a --download
```

To download the first *n* dialogues (e.g., the first 5):
```bash
python src/scripts/download_align_dataset.py --dataset ami --download --n 5
```

To download and align **all** available dialogues in the dataset (Warning: this might take a while):
```bash
python src/scripts/download_align_dataset.py --dataset ami --download
```

If you already have the transcript file locally, provide the `--dialogue_location`:
```bash
python src/scripts/download_align_dataset.py --dataset ami --dialogue_id EN2001a --dialogue_location src/ontology/data/dialog_ami/EN2001a.jsonl
```

**For the DAIC-WOZ dataset:**
Note: Downloading is currently not supported for DAIC-WOZ. You must explicitly provide the dialogue location. This dataset is available by request from [DAIC-WOZ](https://dcapswoz.ict.usc.edu/) for academics and other non-profit researchers.
```bash
python src/scripts/download_align_dataset.py --dataset daicwoz --dialogue_id 301 --dialogue_location src/ontology/data/dialog_daicwoz/301_TRANSCRIPT.csv
```

**Additional Options:**
You can specify a custom output directory using the `--output_dir` parameter for the resulting alignments:
```bash
python src/scripts/download_align_dataset.py --dataset ami --dialogue_id EN2001a --download --output_dir custom/path/
```
