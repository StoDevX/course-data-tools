## getData.py
Before using this script, you'll need a some other libraries:

- Python 3.4 or greater (3.x might work, but I haven't tested)
- beautifulsoup4
- requests
- lxml
- xmltodict

so a `pip3 install beautifulsoup4 requests lxml xmltodict` should do it.

## Usage

`python3 getData.py --years 1994 1995 --terms 20141`

Simply calling `python3 getData.py` will run it on every term from 19941 to the current year.

- The `--years` argument will run it on all five terms for the given years.
- The `--terms` argument will run it on any given terms.
- The `--force` or `-f` argument will force it to update from the server – not ideal, generally, and only to be used when the data needs to be updated.
