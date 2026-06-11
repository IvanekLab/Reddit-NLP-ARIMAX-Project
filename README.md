# Cornell Reddit H5N1 Project

Code for a research project analyzing online discussion of avian flu (H5N1).
It collects Reddit comments and Google News articles about bird flu, runs an
NLP analysis of that discussion (sentiment, toxicity, topic modeling, n-grams),
and models weekly Reddit comment volume over time against external signals such
as news activity, egg prices, and animal-case data.

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
│   ├── Reddit_NLP_Data_Analysis.ipynb
│   └── ARIMAX_modeling.ipynb
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

- `Reddit_NLP_Data_Analysis.ipynb` — data cleaning, EDA, n-grams, sentiment,
  toxicity, and topic modeling.
- `ARIMAX_modeling.ipynb` — ARIMA / ARIMAX time-series modeling of weekly
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
