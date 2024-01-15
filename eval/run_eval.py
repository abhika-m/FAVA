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
from ..utils import remove_error_tags, load_jsonlines, split_sentences, run_detection

# Fava prompt formats
INPUT = "Read the following references:\n{evidence}\nPlease identify all the errors in the following text using the information in the references provided and suggest edits if necessary:\n[Text] {output}\n[Edited] "

def run_eval(args):
    # create output path
    if args.output_file is not None:
        output_dir = os.path.dirname(args.output_file)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    if args.model_name_or_path is not None:
        if args.input_file is not None:
            inputs = json.load(open(args.input_file))
            # format prompts using passage and evidence
            prompts = []
            for input in inputs:
                evidences = []
                if "ctxs" in input:
                    for c in input["ctxs"]:
                        evidences.append(c["text"])
                if "evidence" in input:
                    evidences.append(input["evidence"])

                idx = 1
                for e in evidences:
                    prompt += "Reference [" + str(idx) + "]: " + e + "\n"
                    idx += 1
                prompts.append(
                    INPUT.format_map({"evidence": evidences, "output": input["output"]})
                )
            # populate edited outputs
            model = vllm.LLM(model=args.model_name_or_path)
            sampling_params = vllm.SamplingParams(
                temperature=args.temperature if args.do_sample else 0,
                top_p=args.top_p,
                max_tokens=args.max_new_tokens,
            )
            outputs = model.generate(prompts, sampling_params)

        if args.metric == "factscore":
            fs = FactScorer(model_name="retrieval+ChatGPT", openai_key=args.openai_key)

        for i in range(len(outputs)):
            # calculate factscore
            if args.metric == "factscore":
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
            if args.metric == "detection":
                inputs[i]["edited_output"] = outputs[i]
                error_types = [
                    "<entity>",
                    "<relation>",
                    "<contradictory>",
                    "<unverifiable>",
                    "<invented>",
                    "<subjective>",
                ]
                pred_sentences = split_sentences(outputs[i])
                gold_sentences = split_sentences(inputs[i]["annotated"])
                sentences = min(len(pred_sentences), len(gold_sentences))
                new_inputs = run_detection(
                    gold_sentences[0:sentences], pred_sentences[0:sentences], inputs, i
                )
                inputs = new_inputs

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
        help="Huggingface model name or path.",
    )
    parser.add_argument(
        "--input_file",
        type=str,
        default=None,
        help="Input .json files containing input passages and references and/or titles if using factscore.",
    )
    parser.add_argument(
        "--output_file",
        type=str,
        default="output/result.jsonl",
        help="Output .jsonl file containing passages and scores.",
    )
    parser.add_argument(
        "--metric", type=str, default="factscore", help="Metric for evaluation."
    )
    parser.add_argument(
        "--openai_key", type=str, default=None, help="OpenAI key for factscore."
    )
    parser.add_argument("--max_new_tokens", type=int, default=1024)
    parser.add_argument("--do_sample", action="store_true")
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--top_p", type=float, default=1.0)
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = parse_args()
    run_eval(args)
