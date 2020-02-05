# Media meta data collector

### Getting Started

Make sure Python 3 is installed

```bash
python3 -v
```

Install pips

```bash
pip3 install mutagen requests opencv
```

To Run

First get the ID from TMDb of the Film or TV Show you want data for 

```bash
curl --location --request GET 'https://api.themoviedb.org/3/search/tv?query={{NAME}}?api_key={{API_KEY}}
```

Then using that ID run index.py over the directory (for a TV Show) or the file (for a Film) with the outlined process arguments
A TV Show must already have season and episode number data tagged to the file, or contain a string in the file name that follows a specific format (eg. S01E01 for Season 1, Episode 1)

```bash
python3 index.py {{API_KEY}} /path/to/directory_or_file {{TMDb_ID}}
```