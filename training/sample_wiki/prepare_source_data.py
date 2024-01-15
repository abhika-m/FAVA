import argparse
import random
from doc_db import DocDB
import jsonlines
import requests
import unicodedata
from tqdm import tqdm
import re
headers = {'User-Agent': 'copied user agent that came out when I googled it'}
YEAR = 2022

def normalize(text):
    """Resolve different type of unicode encodings."""
    return unicodedata.normalize('NFD', text)

def cleanup_text(text):
    # add function to remove <ref name=\"USCensusQuickFacts\"></ref>
    clean_text = re.sub(r'<ref.*?>.*?</ref>', '', text)
    return clean_text

def retrieve_top_1000_titles(year, month):
    url = "https://wikimedia.org/api/rest_v1/metrics/pageviews/top/en.wikipedia/all-access/{0}/{1}/all-days".format(
        year, month)
    response = requests.get(url, headers=headers)
    results = response.json()
    print(results)
    top_titles = {}
    for item in results["items"][0]["articles"]:
        title = item["article"]
        if title in ["'Special:Search'", "Main_Page"]:
            continue
        title = title.replace("_", " ")
        top_titles[title] = item["views"]
    return top_titles


def find_top_n_titles_per_year(year, n):
    annual_results = {}
    for month in range(1, 13):
        if month < 10:
            str_month = "0"+str(month)
        else:
            str_month = str(month)
        per_month_result = retrieve_top_1000_titles(year, str_month)
        for title, view in per_month_result.items():
            if title not in annual_results:
                annual_results[title] = view
            else:
                annual_results[title] += view
    sorted_dict = sorted(annual_results.items(),
                         key=lambda x: x[1], reverse=True)
    return [item[0] for item in sorted_dict[:n]]


def save_file_jsonl(data, fp):
    with jsonlines.open(fp, mode='w') as writer:
        writer.write_all(data)

def extract_intro_paragraph(text):
    if text is None:
        return "", ""
    title = text.split("\n\n")[0]
    intro = cleanup_text(text.split("\n\nSection::::")[0])
    print(intro)
    return title, intro

def extract_all_paragraph(text):
    print("not implemented")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('db_path', type=str, help='/path/to/data')
    parser.add_argument('--n', type=int, default=None,
                        help='Number of the sampled passages')
    parser.add_argument('--top', action="store_true",
                        help="sample from Wikipedia's top 1000 articles")
    parser.add_argument('--intro_only', action="store_true",
                        help="sample from Wikipedia's top 1000 articles")
    parser.add_argument('--minimum_k', type=int, default=None,
                        help='Set the minimum article length')
    parser.add_argument('--sample', action="store_true",
                        help="If used with `top` we randomly sample n paragraph form the top 1000 articles; otherwise we just use top n.")
    parser.add_argument('--output_path', type=str, help='/path/to/data')
    args = parser.parse_args()

    db = DocDB(args.db_path)

    if args.top is True:
        print("retrieving top articles")
        sampled_titles = find_top_n_titles_per_year(YEAR, args.n)
        sampled_titles = [normalize(title) for title in sampled_titles]
        print(sampled_titles)
    elif args.top is False and args.minimum_k is not None:
        print("retrieving all titles that meets minimum length")
        all_titles = db.get_doc_title_longer_than_n(args.minimum_k)
        print("randomly sample articles")
        sampled_titles = random.sample(all_titles, k=args.n)
    else:
        print("retrieving all titles")
        all_titles = db.get_doc_title()
        print("randomly sample articles")
        sampled_titles = random.sample(all_titles, k=args.n)
    dataset = []
    for title in tqdm(sampled_titles):
        doc_text = db.get_doc_text(title)
        if args.intro_only is True:
            _, intro  = extract_intro_paragraph(doc_text)
            if len(intro) == 0:
                continue
            dataset.append({"title": title, "intro": intro})
        else:
            paragraphs = extract_all_paragraph(doc_text)
            dataset.append({"title": title, "paragraphs": paragraphs})

    save_file_jsonl(dataset, args.output_path)
