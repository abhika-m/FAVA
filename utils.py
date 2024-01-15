import jsonlines
import tqdm
import json
import time
import os

# loads jsonlines into a list format
def load_jsonlines(file):
    with jsonlines.open(file, 'r') as jsonl_f:
        lst = [obj for obj in jsonl_f]
    return lst

# splits passage into sentences
def split_sentences(text):
    sentences = []
    doc = nlp(text)
    for sent in doc.sents:
        sentences.append(sent.text)
    return sentences
  
# removes <mark>, <delete>, and other error tokens from passage
def remove_error_tags(token_passage):
    error_tokens = ['<entity>', '<relation>', '<contradictory>', '<unverifiable>', '<subjective>', '<invented>', '<mark>',
                    '</entity>', '</relation>', '</contradictory>', '</unverifiable>', '</subjective>', '</invented>', '</mark>']
    for tok in error_tokens:
        token_passage = token_passage.replace(tok, "")
    if "<delete>" not in token_passage:
        return token_passage
    else:
        count = 0
        while "<delete>" in token_passage and "</delete>" in token_passage and count < 10:
            next_delete_start_index = token_passage.index("<delete>")
            next_delete_end_index = token_passage.index("</delete>")
            deleted_part = token_passage[next_delete_start_index:(next_delete_end_index + 9)]
            token_passage = token_passage.replace(deleted_part, "")
            count += 1

    token_passage = token_passage.replace("</s>", "")
    return token_passage
    
def swap_error_tags(token_passage):
    token_passage = token_passage.replace("<mark>", "<d>")
    token_passage = token_passage.replace("</mark>", "</d>")
    token_passage = token_passage.replace("<delete>", "<mark>")
    token_passage = token_passage.replace("</delete>", "</mark>")
    token_passage = token_passage.replace("<d>", "<delete>")
    token_passage = token_passage.replace("</d>", "</delete>")
    token_passage = token_passage.replace("<contradictory>", "<contradictory><delete>")
    token_passage = token_passage.replace("</contradictory>", "</delete><contradictory>")
    print(token_passage)
    token_passage = token_passage.replace("</s>", "")
    return token_passage
    
def run_detection(gold_sentences, pred_sentences, inputs, i) :
  for idx, (s_g, s_p) in enumerate(zip(gold_sentences, pred_sentences)):
    results_rec.setdefault(idx, {}) 
    results_prec.setdefault(idx, {}) 
    for e in error_types: 
      results_prec[idx].setdefault(e, -1)
      results_rec[idx].setdefault(e, -1)
      if e in s_g:
        correct = 1 if e in s_p else 0
        results_rec[idx][e] = correct
      if e in s_p:
        correct = 1 if e in s_g else 0
        results_prec[idx][e] = correct
  per_error_average_prec = {}
  per_error_average_rec = {}
  for e in error_types:
    counts_p = []
    counts_r = []
    for s_idx in results_prec:
      if results_prec[s_idx][e]> -1:
        counts_p.append(results_prec[s_idx][e])
    for s_idx in results_rec:
      if results_rec[s_idx][e]> -1:
        counts_r.append(results_rec[s_idx][e])
    if(len(counts_p) != 0):
      per_error_average_prec[e] = np.mean(counts_p)
    if(len(counts_r) != 0):
      per_error_average_rec[e] = np.mean(counts_r)
              
  inputs[i]["per_error_prec"] = per_error_average_prec
  inputs[i]["per_error_rec"] = per_error_average_rec
  counts = []
  for r in per_error_average_prec.values():
    counts.append(r)
  if len(counts) == 0:
    overall_average = -1
  else:
    overall_average = np.mean(counts)
  inputs[i]["overall_prec"] = overall_average
  counts = []
  for r in per_error_average_rec.values():
    counts.append(r)
  if len(counts) == 0:
    overall_average = -1
  else:
    overall_average = np.mean(counts)
  inputs[i]["overall_rec"] = overall_average
  return inputs
