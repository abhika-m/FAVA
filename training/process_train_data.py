import json
import argparse
import random
from ..utils import swap_error_tags, remove_error_tags

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input_file",
        type=str,
        default=None,
        help="Input .json file with title and input fields to generate training data")
    parser.add_argument(
        "--output_file",
        type=str,
        default=None,
        help="Input .json file with title and input fields to generate training data")
    args = parser.parse_args()
    return args
  
def process(file, output_file):
  data = json.load(open(file))
  result = []
  for d in data:
    evidences = []
    if "ctxs" in d:
      for c in d["ctxs"]:
        evidences.append(c["text"])
    if "evidence" in d:
      evidences.append(d["evidence"])
    
    random.shuffle(evidences)
    completion = swap_error_tags(d["errored_passage"])
    errored = remove_error_tags(d["errored_passage"])

    prompt = "Read the following references:\n"
    idx = 1
    for e in evidences:
      prompt += "Reference [" + str(idx) + "]: " + e + "\n"
      idx += 1
    prompt += "Please identify all the errors in the following text using the information in the references provided and suggest edits:\n[Text] "
    prompt += errored
    prompt += "\n[Edited] "
    result.append({"prompt": prompt, "input": "", "completion": completion})

  # create json file with data
  json_object = json.dumps(result)
  with open(output_file, "w") as outfile:
      outfile.write(json_object)
    
if __name__ == "__main__":
    args = parse_args()
    if(args.output_file == None):
      args.output_file = args.input_file

    process(args.input_file, args.output_file)
    
    
