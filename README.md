# FAVA

[![made-with-python](https://img.shields.io/badge/Made%20with-Python-red.svg)](#python)

## Install
```
conda create -n fava python=3.9
conda activate fava
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

## Running Evals

We provide two main evaluation set ups: FActScore and our own fine grained error detection task. To run either evaluation system, you must have an input jsonl file with "passage" and "reference" fields. To run FActScore, you must also have a "title" field for each instance. To run the detection task, you must additionally have a gold annotations file with the gold edits.

### Data Format
When running evals you will need to provide an input file of type jsonl. Each instance in the input file should include a passage and a reference for that passage. When running FActScore, you also need to provide a title field. For the detection task, you must also provide a gold annotation file consisting of the gold annotations to compare to.

### FActScore
```bash
cd eval
python run_eval --model_name_or_path {model_name_or_path} --input_file {input_passages_references_titles} --output_file {output_file_path} --metric factscore --openai_key {your_openai_key}
```

Input File Example: `{"passage": "Lionel Andrés Messi, also known as Leo Messi, is an American professional footballer who plays as a forward.", "reference": "Lionel Messi is an Argentine soccer player.", "title": "Lionel Messi"}, ...`

### Fine Grained Sentence Detection
```bash
cd eval
python run_eval --model_name_or_path {model_name_or_path} --input_file {input_passages_references_titles} --gold_annotations_file {gold_annotated_passages} --output_file {output_file_path} --metric detection
```

Input File Example: `{"passage": "Lionel Andrés Messi, also known as Leo Messi, is an American professional footballer who plays as a forward.", "reference": "Lionel Messi is an Argentine soccer player."}, ...`

Gold Annotation File Example: `{"passage": "Lionel Andrés Messi, also known as Leo Messi, is an <entity><delete>American</delete><mark>Argentine</mark></entity> professional footballer who plays as a forward."}, ...`

**Optional flags**:
- `--max_new_tokens`: max new tokens to generate
- `--do_sample`: true or false, whether or not to use sampling
- `--temperature`: temperature for sampling
- `--top_p`: top_p value for sampling
