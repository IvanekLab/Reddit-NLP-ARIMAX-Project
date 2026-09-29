# Cornell Reddit H5N1 Project

Code for a research project analyzing online discussion of avian flu (H5N1).
It collects Reddit comments and Google News articles about bird flu, runs an
NLP analysis of that discussion (sentiment, toxicity, topic modeling, n-grams),
and models weekly Reddit comment volume over time against external signals such
as news activity, egg prices, and animal-case data.

## Associated publication

This repository contains the code accompanying:

> Dalla Pria, L., Nelson, A. L., Koebel, K. J., & Ivanek, R. (2026). 
> Mammalian spillover events predict the volume and emotion of online 
> discourse during the US H5N1 outbreak. TBD.

Archived version: [Zenodo DOI 10.5281/zenodo.XXXXXXX](https://doi.org/10.5281/zenodo.XXXXXXX)

## Repository structure

```
cornell-reddit-h5n1-project/
├── README.md
├── requirements.txt           # All dependencies (collection + analysis)
├── src/                       # Data collection scripts
│   ├── reddit_collection.py
│   ├── google_news_collection.py
│   └── .env.example
├── notebooks/                 # Analysis and modeling
│   ├── Luizza_Reddit_NLP_Data_Analysis_2026.ipynb
│   └── Luizza_ARIMAX_Modeling_2026.ipynb
└── figures/                   # Generated charts
```

## Setup

```bash
pip install -r requirements.txt
python -m nltk.downloader stopwords punkt punkt_tab wordnet vader_lexicon
```

## 1. Collect the data (`src/`)

Pulls the raw data from the Reddit and Google News (SerpApi) APIs. You need your
own API keys:

- Reddit: create an app at https://www.reddit.com/prefs/apps
- SerpApi: get a key at https://serpapi.com

Copy `src/.env.example` to `src/.env` and fill in your keys, then run:

```bash
python src/reddit_collection.py        # -> df_birdflu.csv, df_h5n1.csv, df_birdflupreps.csv
python src/google_news_collection.py   # -> serpapi_birdflu_news.csv
```

Collection can take a while and may pause for API rate limits — this is normal.

## 2. Run the analysis (`notebooks/`)

Open the notebooks in VS Code or Jupyter:

- `Luizza_Reddit_NLP_Data_Analysis_2026.ipynb` — data cleaning, EDA, n-grams, sentiment,
  toxicity, and topic modeling.
- `Luizza_ARIMAX_Modeling_2026.ipynb` — ARIMA / ARIMAX time-series modeling of weekly
  comment volume.

## Data files

The notebooks read CSVs produced by the collection scripts plus a few external
sources (egg prices, poultry / cattle / mammal / wild-bird cases). Place these
files where the notebooks expect them (paths are set near the top of each
notebook). Because API results change over time, re-running collection produces
fresh data; to reproduce the published findings, use the CSV snapshots included
with the research.

## Notes

- API keys are loaded from a local `.env` file and are never committed.
- `.gitignore` excludes `.env`, data files (`*.csv`), and Python caches.

## Citation

If you use this code, please cite:

> Dalla Pria, L. et al. (2026). Mammalian spillover events predict the volume 
> and emotion of online discourse during the US H5N1 outbreak. TBD. DOI: [paper DOI once available]

## License

This project is licensed under the terms of the LICENSE file in this repository.

## Contact

For questions, contact Luizza Dalla Pria (ln326@cornell.edu).
