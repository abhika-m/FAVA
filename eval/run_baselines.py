import argparse
import json
import os
import numpy as np
import time
import backoff
import openai
import tiktoken
from ..utils import remove_error_tags, load_jsonlines, split_sentences, run_detection

@backoff.on_exception(backoff.expo, openai.error.RateLimitError)
@backoff.on_exception(backoff.expo, openai.error.ServiceUnavailableError)
def completions_with_backoff(**kwargs):
    return openai.ChatCompletion.create(**kwargs)
  
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model_name",
        type=str,
        default=None,
        help="OpenAI model name.",
    )
    parser.add_argument(
        "--input_file",
        type=str,
        default=None,
        help="Input .json file containing input passages and references.",
    )
    parser.add_argument(
        "--output_file",
        type=str,
        default="output/result.json",
        help="Output .json file containing passages and edits.",
    )
    parser.add_argument(
        "--openai_key", type=str, default=None, help="OpenAI key for factscore."
    )
  parser.add_argument(
        "--retrieval", action="store_true"
    )
   args = parser.parse_args()
  return args
  
# constructs prompt for LM, if evidence is not empty string, then includes it (retrieval)
def get_prompt(output, evidence):
    prompt = ""
    prompt += "Given a passage with factual errors, identify any <entity>, <relation>, <contradictory>, <subjective>, <unverifiable> or <invented> errors in the passage and add edits for <entity> and <relation> errors by inserting additional <mark></mark> or <delete></delete> tags.  If there are no errors, return the passage with no tags. Any changes to the original passage should be marked in <> tags. Below are the error definitions followed by examples of what you need to follow.\n"
    prompt += "Definitions:\n"
    prompt += "1. entity errors (<entity>): a small part of a sentence, often an entity (e.g., location name), is incorrect (usually 1-3 words). Entity errors often involve noun phrases or nouns.\n"
    prompt += "2. relational error (<relation>): a sentence is partially incorrect as a small part (usually 1 - 3 words). Relational errors often involve verbs and are often the opposite of what it should be.\n"
    prompt += "3. contradictory sentence error (<contradictory>): a sentence where the entire sentence is contradicted by the given reference, meaning the sentence can be proven false due to a contradiction with information in the passage.\n"
    prompt += "4. invented info error (< invented >): these errors refer to entities that are not known  or do not exist. This does not include fictional characters in books or movies. made-up info errors include phrases or sentences which have unknown entities or misleading information.\n"
    prompt += "5. subjective sentence (<subjective>): an entire sentence or phrase that is subjective and cannot be verified, so it should not be included.\n"
    prompt += "6. unverifiable sentence (<unverifiable>): a sentence where the whole sentence or phrase is unlikely to be factually grounded although it can be true, and the sentence cannot be confirmed nor denied using the reference given or internet search, it is often something personal or private and hence cannot be confirmed.\n"
    prompt += "Follow the given example exactly, your task is to create the edited completion with error tags <>:\n##\n"
    prompt += "Passage: Marooned on Mars is a science fiction novel aimed at a younger audience. It was written by Andy Weir and published by John C. Winston Co. in 1952, featuring illustrations by Alex Schomburg. It ended up having a readership of older boys despite efforts for it to be aimed at younger kids .The novel inspired the famous Broadway musical \"Stranded Stars,\" which won six Tony Awards. The novel tells a story of being stranded on the Purple Planet. I wish the novel had more exciting and thrilling plot twists.\n"
    if len(evidence) > 1:
        prompt += "Reference: Marooned on Mars is a juvenile science fiction novel written by American writer Lester del Rey. It was published by John C. Winston Co. in 1952 with illustrations by Alex Schomburg.\n"
    prompt += "Edited: Marooned on Mars is a science fiction novel aimed at a younger audience. It was written by <entity><mark>Lester del Rey</mark><delete>Andy Weir</delete></entity> and published by John C. Winston Co. in 1952, featuring illustrations by Alex Schomburg. <contradictory>It ended up having a readership of older boys despite efforts for it to be aimed at younger kids .</contradictory>. <invented>The novel inspired the famous Broadway musical \"Stranded Stars,\" which won six Tony Awards.</invented> The novel tells a story of being stranded on the <entity><mark>Red</mark><delete>Purple</delete></entity> Planet. <subjective>I wish the novel had more exciting and thrilling plot twists.</subjective>\n"
    prompt += "##\n"
    prompt += "##\n Now detect errors and include edits in the following passage like done in the example above. Include error tags <> for ANYTHING YOU CHANGE IN THE ORIGINAL PASSAGE.\n\n"
    prompt += "Passage: " + output
    if len(evidence) > 1:
        prompt += "\nReference: " + evidence
    prompt += "\nEdited: "
    print(prompt)
    return prompt

def run_gpt_baseline(file, out, model, retrieval):
    preds = json.load(open(file))        
    usage = 0
    data = []
    encoding = tiktoken.encoding_for_model(model)
    idx = 0
    for q in preds:
        output = q["output"]
        evidence = q["reference"]
        prompt = get_prompt(output, evidence)
        tokens = encoding.encode(prompt)
        token = 4000 - len(tokens)
        if token < 0:
            prompt = get_prompt(output, evidence[0:300])
            tokens = encoding.encode(prompt)
            token = 4000 - len(tokens)
        try:
            response = completions_with_backoff(
                model=model,
                messages=[
                {"role": "user", "content": prompt}
                ],
                max_tokens=token)
        except:
          print("sleeping...")
            time.sleep(60)
            response = completions_with_backoff(
                model=model,
                messages=[
                {"role": "user", "content": prompt}
                ],
                max_tokens=token)
        usage += ((response.usage.total_tokens / 1000) * 0.002)
        print("cost: {0}: ".format(usage))
        passage = response.choices[0].message.content
        if len(passage) < 50:
            passage = output
        q["chat_gpt_edited"] = passage
        idx += 1
    with open(out + ".json", "w") as outfile:
            json.dump(preds, outfile)

if __name__ == "__main__":
    args = parse_args()
    openai.api_key = args.openai_key
    run_gpt_baseline(args.input_file, args.output_file, args.model_name, args.retrieval)
    
