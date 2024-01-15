# FAVA

[![made-with-python](https://img.shields.io/badge/Made%20with-Python-red.svg)](#python)

## Install
```
conda create -n fava python=3.9
conda activate fava
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```
## Training 

### Step 1: Synthetic Data Generation

Our synthetic data generation takes in wikipedia passages and a title, diversifies the passage to another genre of text and then inserts errors one by one using ChatGPT and GPT-4.

#### Input Data Format
The input data should be a .jsonl file including "intro" and "title" where "intro" is the introduction of a sampled Wikipedia passage and "title" is the topic of the passage.

#### Output Data Format
The output data of the data generation script will be a .json file including the original passage as "evidence", the diversified text as "diversified_passage", the passage with inserted errors as "errored_passage", the subject of the passage as "subject", the genre of text diversification as "type", and the different error types inserted as "error_types".

#### Running Data Generation
```bash
cd training
python generate_train_data.py --input_file {input_file_path} --output_file {output_file_path} --openai_key {your_openai_key}
```

### Step 2: Process Training Data

#### Input Data Format
The input data should be a .json file including "errored_passage" as the passage with inserted errors and "evidence" as the base wikipedia article from step 1. This file can also include "ctxs" as additional evidence passages. 

#### Output Data Format
The output data of the data generation script will be a .json file with "prompt" and "completion" as the set up for training.

#### Running Data Generation
```bash
cd training
python process_train_data.py --input_file {input_file_path} --output_file {output_file_path}
```
### Step 3: Training
We followed [Open-Instruct's](https://github.com/allenai/open-instruct) training script for training FAVA. We updated and ran [this script](https://github.com/allenai/open-instruct/blob/main/scripts/finetune_with_accelerate.sh) updating the train_file to our processed training data from step 2 and used Llama-2-Chat 7B as our base model.

## Running Evals

We provide two main evaluation set ups: FActScore and our own fine grained error detection task. 

### Input Data Format

To run either evaluation system, you must have an input json file with "output" and "evidence" fields. To run FActScore, you must also have a "title" field for each instance. To run the detection task, you must additionally have a "annotated" field with the gold edits.

### FActScore
```bash
cd eval
python run_eval --model_name_or_path {model_name_or_path} --input_file {input_passages_references_titles} --output_file {output_file_path} --metric factscore --openai_key {your_openai_key}
```

Input File Example: `{"passage": "Lionel Andrés Messi, also known as Leo Messi, is an American professional footballer who plays as a forward.", "reference": "Lionel Messi is an Argentine soccer player.", "title": "Lionel Messi"}, ...`

### Fine Grained Sentence Detection
```bash
cd eval
python run_eval --model_name_or_path {model_name_or_path} --input_file {input_passages_references_titles} --output_file {output_file_path} --metric detection
```

Input File Example: `{"passage": "Lionel Andrés Messi, also known as Leo Messi, is an American professional footballer who plays as a forward.", "reference": "Lionel Messi is an Argentine soccer player.", "annotated": "Lionel Andrés Messi, also known as Leo Messi, is an <entity><delete>American</delete><mark>Argentine</mark></entity> professional footballer who plays as a forward}", ...`

**Optional flags**:
- `--max_new_tokens`: max new tokens to generate
- `--do_sample`: true or false, whether or not to use sampling
- `--temperature`: temperature for sampling
- `--top_p`: top_p value for sampling

## Citation

We used Open-Instruct's training code:

```bibtex
@misc{wang2023far,
   title={How Far Can Camels Go? Exploring the State of Instruction Tuning on Open Resources}, 
   author={Yizhong Wang and Hamish Ivison and Pradeep Dasigi and Jack Hessel and Tushar Khot and Khyathi Raghavi Chandu and David Wadden and Kelsey MacMillan and Noah A. Smith and Iz Beltagy and Hannaneh Hajishirzi},
   year={2023},
   eprint={2306.04751},
   archivePrefix={arXiv},
}
```

```bibtex
@misc{ivison2023camels,
      title={Camels in a Changing Climate: Enhancing LM Adaptation with Tulu 2}, 
      author={Hamish Ivison and Yizhong Wang and Valentina Pyatkin and Nathan Lambert and Matthew Peters and Pradeep Dasigi and Joel Jang and David Wadden and Noah A. Smith and Iz Beltagy and Hannaneh Hajishirzi},
      year={2023},
      eprint={2311.10702},
      archivePrefix={arXiv},
}
```

We use FActScore for editing evaluations:

```bibtex
@inproceedings{factscore,
    title={ {FActScore}: Fine-grained Atomic Evaluation of Factual Precision in Long Form Text Generation },
    author={ Min, Sewon and Krishna, Kalpesh and Lyu, Xinxi and Lewis, Mike and Yih, Wen-tau and Koh, Pang Wei and Iyyer, Mohit and Zettlemoyer, Luke and Hajishirzi, Hannaneh },
    year={ 2023 },
    booktitle = { EMNLP },
    url={ https://arxiv.org/abs/2305.14251 }
}
```
