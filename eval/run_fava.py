import argparse
import json
import os
import numpy as np
import vllm
import torch
from ..utils import load_jsonlines

# Fava prompt
INPUT = "Read the following references:\n{evidence}\nPlease identify all the errors in the following text using the information in the references provided and suggest edits if necessary:\n[Text] {output}\n[Edited] "

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
      help="Input .jsonl files containing passage and reference.")
  args = parser.parse_args()
  return args

if __name__ == "__main__":
  args = parse_args()
  model = vllm.LLM(model=args.model_name_or_path)
  sampling_params = vllm.SamplingParams(
    temperature=args.temperature if args.do_sample else 0,
    top_p=args.top_p,
    max_tokens=args.max_new_tokens,
  )
  outputs = model.generate(prompts, sampling_params)
  outputs = [it.outputs[0].text for it in outputs]
  print(outputs[0])

  

