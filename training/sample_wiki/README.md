# Wikipedia preprocessing
This directory contains the codes to pre-process Wikipedia dump.

## Overview 
1. [Download Wikipedia dump](#download-dump)
2. [Extract Wikipedia data](#extract-data) 
3. [Build sqlite3 DB](#build-db)
4. [Load data from the DB](#load-data)

### Download dump
You first need to download the Wikipedia dump file. The most up-to-date dump files are available at [enwiki](https://dumps.wikimedia.org/enwiki/). Make sure to download the file including the full article data, which is titled as `enwiki-[time]-pages-artciles-multistream.xml.bz2`. 

For instance, the 2023 January Wikipedia can be downloaded at [enwiki-20230101-pages-articles-multistream.xml.bz2](https://dumps.wikimedia.org/enwiki/20230101/enwiki-20230101-pages-articles-multistream.xml.bz2)

```
wget https://dumps.wikimedia.org/enwiki/20230101/enwiki-20230101-pages-articles-multistream.xml.bz2
```

### Extract data
Once dump data is downloaded, the article data needs to be extracted. [wikiextractor](https://github.com/attardi/wikiextractor) is recommended.

```
git clone https://github.com/attardi/wikiextractor.git
cd wikiextractor/wikiextractor
python Wikiextractor /path/to/your/dump --json --o enwiki20330101 
```

### Build DB
The wikiextractor scripts generate many json files in dozens of different directories, which is not ideal for quite data retrieval. Run sqlite3 DB file for future preprocessing. 
```
python build_db.py /path/to/your/wikiextractor/result/enwiki20330101 enwiki20230101.db
```

### Load data
There's a pre-defined `DocDB` class in [doc_db.py](doc_db.py) and you can easily call and load the text data. 

```
from doc_db import DocDB
db = DocDB("path/to/your/db")
text = db.get_doc_text("Canada")
wikipedia_id = db.get_doc_id("Canada")
all_titles = db.get_doc_title() # this will collect all of the titles and is really slow. 
long_wiki_titles = db.get_doc_title_longer_than_n(n=10000) # collect wikipedia titles longer than 10000 characters. 
```

You can create a source Wikipedia file using `prepare_source_data.py`. Currently this script support two different approaches to sample articles from 6M+ English Wikipedia. 

- Sample articles from 1,000 most viewed articles

This method call wikipedia rest API to collect the top 1k articles from 2022. You can change the global variable `YEAR` to change the default year. 
```
python prepare_source_data.py enwiki2023.db --n 1000 --top --intro_only  --output_path enwiki_1k_from_top_1k.jsonl
```

- randomly sample from articles with more than 10k characters

Often longer Wikipedia articles are high-quality and are frequently edited by many volunteers. You can specify the minimum characters and randomly sample articles.  
```
python prepare_source_data.py enwiki2023.db --n 1000 --intro_only --minimum_k 10000 --output_path enwiki_minimum_sample.jsonl
```
