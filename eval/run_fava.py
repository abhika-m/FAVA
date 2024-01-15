import argparse
import json
import os
import numpy as np
import vllm
import torch
from ..utils import load_jsonlines

# Fava prompt
INPUT = "Read the following references:\n{evidence}\nPlease identify all the errors in the following text using the information in the references provided and suggest edits if necessary:\n[Text] {output}\n[Edited] "

if __name__ == "__main__":
    args = parse_args()
    
    model = vllm.LLM(model="fava-uw/fava-model")
    sampling_params = vllm.SamplingParams(
        temperature=0,
        top_p=1.0,
        max_tokens=1024,
    )
    output = "" # add your passage to verify
    evidence = "" # add a piece of evidence
    prompts = [INPUT.format_map({"evidence": evidence, "output": output})]
    outputs = model.generate(prompts, sampling_params)
    outputs = [it.outputs[0].text for it in outputs]
    print(outputs[0])
