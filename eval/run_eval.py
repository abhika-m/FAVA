from factscore.factscorer import FactScorer
import os
import json
import tqdm
import jsonlines
import numpy as np
import openai
import backoff
import time
import argparse
import vllm
import spacy
nlp = spacy.load("en_core_web_sm")
from utils import remove_error_tags, generate_completions, load_hf_lm_and_tokenizer, load_jsonlines, split_sentences, run_detections

# Fava prompt formats
INPUT = "Read the following references:\n{evidence}\nPlease identify all the errors in the following text using the information in the references provided and suggest edits if necessary:\n[Text] {output}\n[Edited] "
QA = "Read the following references:\n{evidence}\nPlease identify all the errors in the following text using the information in the references provided and suggest edits:\n[Text] Question: {question} Answer: {output}\n[Edited] "
      
def run_eval(args) :
  # create output path
  if args.output_file is not None:
        output_dir = os.path.dirname(args.output_file)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

  if args.model_name_or_path is not None:
    if args.input_file is not None:
      inputs = load_jsonlines(args.input_file)
      # format prompts using passage and evidence
      prompts = [INPUT.format_map({"evidence":input["evidence"], "output":input["passage"]}) for input in inputs]
      # populate edited outputs

      model = vllm.LLM(model=args.model_name_or_path)
      sampling_params = vllm.SamplingParams(
          temperature=args.temperature if args.do_sample else 0,
          top_p=args.top_p,
          max_tokens=args.max_new_tokens,
        )
      outputs = model.generate(prompts, sampling_params)
      
    if args.metric == 'factscore':
      fs = FactScorer(model_name="retrieval+ChatGPT", openai_key=args.openai_key)

    for i in range(len(outputs)):
      # calculate factscore
      if args.metric == 'factscore':
        title = inputs[i]["title"]
        edited_output = remove_error_tags(outputs[i])
        try:
          metric_result = fs.get_score([title], [edited_output], gamma=10)
        except:
          try:
            print("sleeping for 60s...")
            time.sleep(60)
            metric_result = fs.get_score([title], [edited_output], gamma=10)
          except:
            metric_result = -1
        inputs[i]["edited_output"] = outputs[i]
        inputs[i]["factscore"] = metric_result
      # calculate fine grained error detection result
      if args.metric == 'detection':
        gold_passages = load_jsonlines(args.gold_annotations_file)
        error_types = ["<entity>", "<relation>", "<contradictory>", "<unverifiable>", "<invented>", "<subjective>"]
        pred_sentences = split_sentences(outputs[i])
        gold_sentences = split_sentences(gold_passages[i])
        sentences = min(len(pred_sentences), len(gold_sentences))
        new_inputs = run_detection(gold_sentences[0:sentences], pred_sentences[0:sentences], inputs, i)
        inputs = new_inputs
        inputs[i]["edited_output"] = outputs[i]
        inputs[i]["gold_annotation"] = gold_passages[i]
    with open(args.output_file, "w") as f:
      for input in inputs:
        f.write(json.dumps(instance) + "\n")
  print("done")

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model_name_or_path",
        type=str,
        default=None,
        help="Huggingface model name or path.")
    parser.add_argument(
        "--input_file",
        type=str,
        default=None,
        help="Input .jsonl files containing input passages and references and/or titles if using factscore.")
    parser.add_argument(
        "--gold_annotations_file",
        type=str,
        default=None,
        help="Input .jsonl files containing annotated passages and references for detection task.")
    parser.add_argument(
        "--output_file",
        type=str,
        default="output/result.jsonl",
        help="Output .jsonl file containing passages and scores.")
    parser.add_argument(
        "--metric",
        type=str,
        default="factscore",
        help="Metric for evaluation.")
    parser.add_argument(
        "--openai_key",
        type=str,
        default=None,
        help="OpenAI key for factscore.")
  parser.add_argument(
        "--max_new_tokens",
        type=int,
        default=1024)
    parser.add_argument(
        "--do_sample",
        action="store_true")
    parser.add_argument(
        "--temperature",
        type=float,
        default=1.0)
    parser.add_argument(
        "--top_p",
        type=float,
        default=1.0)
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = parse_args()
    run_eval(args)



