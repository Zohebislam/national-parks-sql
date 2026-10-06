# Getting the data

Put these three files in `data/raw/`:

| File | Source | How |
|------|--------|-----|
| `national_parks.csv` | TidyTuesday 2019-09-17 (NPS visitation 1904–2016) | downloaded automatically by `python run.py download` |
| `parks.csv` | Kaggle: nationalparkservice/park-biodiversity | see below |
| `species.csv` | same Kaggle dataset | see below |

**Kaggle, option A (browser):** sign in at
https://www.kaggle.com/datasets/nationalparkservice/park-biodiversity, click **Download**,
and drop the resulting `archive.zip` (or the two CSVs) into `data/raw/`. The download
script unzips it for you.

**Kaggle, option B (CLI):** `pip install kaggle`, create an API token at
kaggle.com → Settings → *Create New Token*, save it to `~/.kaggle/kaggle.json`, then run
`python run.py download`.

Raw files are git-ignored; only the code that produces results is committed.
