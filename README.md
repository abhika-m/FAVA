# FAVA

[![made-with-python](https://img.shields.io/badge/Made%20with-Python-red.svg)](#python)

## Intro

FAVA is a hallucination detection and editing model. You can find a model demo [here](https://huggingface.co/spaces/fava-uw/fava), model weights [here](https://huggingface.co/fava-uw/fava-model) and our datasets [here](https://huggingface.co/datasets/fava-uw/fava-data). This repo includes information on synthetic data generation for training and evaluating FAVA.

<p align="center"><img src="https://github.com/abhika-m/FAVA/blob/main/fava.png" alt="FAVA" width="500"/></p>

## Overview 
1. [Installation](#install)
2. [Synthetic Data Generation](#step-1-synthetic-data-generation) 
3. [Postprocess Data for Training](#step-2-process-training-data)
4. [Retrieval Guide](#retrieval-guide)
5. [FActScore Evaluations](#factscore)
6. [Fine Grained Sentence Detection Evaluations](#fine-grained-sentence-detection)

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

#### Running Data Generation
```bash
cd training
python generate_train_data.py \
--input_file {input_file_path} \
--output_file {output_file_path} \
--openai_key {your_openai_key}
```
Input file is `jsonl` and includes:
- `intro` (ex: 'Lionel Messi is an Argentine soccer player.')
- `title` (ex: 'Lionel Andrés Messi')

Output file includes:
- `evidence` (ex: 'Lionel Messi is an Argentine soccer player.')
- `diversified_passage` (ex: 'The Argentine soccer player, Lionel Messi, is...')
- `errored_passage` (ex: 'The \<entity>\<delete>Argentine\</delete>\<mark>American\</mark>\</entity> soccer player, Lionel Messi, is...')
- `subject` (ex: 'Lionel Andrés Messi')
- `type` (ex: 'News Article')
- `error_types` (ex: ['entity'])


### Step 2: Process Training Data

#### Post Processing
```bash
cd training
python process_train_data.py \
--input_file {input_file_path} \
--output_file {output_file_path}
```

Input file is `json` and includes:
- `evidence` (ex: 'Lionel Messi is an Argentine soccer player.')
- `errored_passage` (ex: 'The \<entity>\<delete>Argentine\</delete>\<mark>American\</mark>\</entity> soccer player, Lionel Messi, is...')
- `ctxs` (ex: [{'id': 0, 'title': 'Lionel Messi', 'text': 'Lio Messi is known for...'},...])

Output file includes:
- `prompt` (ex: 'Read the following references:\nReference[1]:Lio Messi is...[Text] The American soccer player, Lionel Messi, is...')
- `completion` (ex: 'The \<entity>\<mark>Argentine\</mark>\<delete>American\</delete>\</entity> soccer player, Lionel Messi, is...')

### Step 3: Training
We followed [Open-Instruct's](https://github.com/allenai/open-instruct) training script for training FAVA. We updated and ran [this script](https://github.com/allenai/open-instruct/blob/main/scripts/finetune_with_accelerate.sh) updating the train_file to our processed training data from step 2 and used Llama-2-Chat 7B as our base model.

You can find our training data [here](https://huggingface.co/datasets/fava-uw/fava-data/blob/main/training.json).

## Retrieval Guide
We use [Contriever](https://github.com/facebookresearch/contriever) to retrieve documents.

### Step 1: Download data
Download the preprocessed passage data and the generated passaged ([Contriever-MSMARCO](https://huggingface.co/facebook/contriever-msmarco)). 
```
cd retrieval
wget https://dl.fbaipublicfiles.com/dpr/wikipedia_split/psgs_w100.tsv.gz
wget https://dl.fbaipublicfiles.com/contriever/embeddings/contriever-msmarco/wikipedia_embeddings.tar
```

### Step 2: Collect Retrieved Passages

We retrieve the top 5 documents but you may adjust `num_docs` as per your liking.
```
cd retrieval
python passage_retrieval.py \
    --model_name_or_path facebook/contriever-msmarco --passages psgs_w100.tsv \
    --passages_embeddings "wikipedia_embeddings/*" \
    --data {input_file_path}  \
    --output_dir {output_file_path} \
    --n_docs {num_docs}
```

Input file is either a `json` or `jsonl` and includes:
- `question` or `instruction` (ex: 'Who is Lionel Messi')


## Evaluations

We provide two main evaluation set ups: FActScore and our own fine grained error detection task. 

### FActScore
```bash
cd eval
python run_eval --model_name_or_path {model_name_or_path} --input_file {input_file_path} --output_file {output_file_path} --metric factscore --openai_key {your_openai_key}
```

Input file is `json` and includes:
- `passage` (ex: 'The American soccer player, Lionel Messi, is...')
- `evidence` (ex: 'Lionel Messi is an Argentine soccer player...')
- `title` (ex: 'Lionel Messi')

[FActScore](https://github.com/shmsw25/FActScore) dataset can be downloaded from [here](https://github.com/shmsw25/FActScore?tab=readme-ov-file#download-the-data). We used the the Alpaca 7B, Alpaca 13B, and ChatGPT data from FActScore.

### Fine Grained Sentence Detection
```bash
cd eval
python run_eval --model_name_or_path {model_name_or_path} --input_file {input_file_path} --output_file {output_file_path} --metric detection
```
Input file is `json` and includes:
- `passage` (ex: 'The American soccer player, Lionel Messi, is...')
- `evidence` (ex: 'Lionel Messi is an Argentine soccer player...')
- `annotated` (ex: 'The \<entity>\<mark>Argentine\</mark>\<delete>American\</delete>\</entity> soccer player, Lionel Messi, is...')


You can find our human annotation data [here](https://huggingface.co/datasets/fava-uw/fava-data/blob/main/annotations.json).

**Optional flags**:
- `--max_new_tokens`: max new tokens to generate
- `--do_sample`: true or false, whether or not to use sampling
- `--temperature`: temperature for sampling
- `--top_p`: top_p value for sampling

## Citation

```bibitex
@article{mishra2024finegrained,
    title={ Fine-grained Hallucinations Detections },
    author={ Mishra, Abhika and Asai, Akari and Balachandran, Vidhisha and Wang, Yizhong and Neubig, Graham and Tsvetkov, Yulia and Hajishirzi, Hannaneh },
    journal={arXiv preprint},
    year={ 2024 },
    url={ https://arxiv.org/abs/2401.06855 }
}
```
