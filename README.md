# openADR 3.1 Static VTN

A generator for static files representing a valid non-authenticating
openADR 3.1 VTN (Virtual Top Node).

When providing more than one 'program' at a time, a CGI script (any variant
will do) or clever URL rewriting in the server is
necessary for the filtering and pagination required by the specification.
The data itself, however, is always static.

This approach enables efficient energy price distribution via static
files served by any standard HTTP server.


## Overview

This project provides a tool that generates openADR 3.1 compliant JSON files
from time-series data. It also includes a collection of static (example)
files containing the metadata necessary to actually comply with the standard.

Actual compliance with the specification also depends heavily on the
configuration of the HTTP server. – For example, the specification requires
that a JSON object be returned instead of HTML for 404 errors. 


## Project Structure

```
.
├── README.md
├── csv2event.py             # The core module and executable
├── generate_index           # Program to generate proper 'index.json' files
└── static_vtn/              # The static metadata files in a proper folder structure
    └── programs/
        └── default-price    # Example file copy/edit for your use case
```


## Usage

### Generate a simple price event file
Let's assume you have already edited `static_vtn/programs/default-price`
for your use case, and the file `prices.csv` contains the time-series data
with a timestamp (ISO 8601 format, e.g., `2024-01-01T08:00:00Z`) in the first
column and the actual price value in the second:

```bash
python3 csv2event.py prices.csv static_vtn/programs/default-price
./generate_index static_vtn/events/
```

`csv2event.py` automatically determines the output location based on the
program file (second argument). For information on more direct control,
use `csv2event.py -h`.

You can find an example of an input file at [[example_prices.csv]].

### Writing custom generators
`csv2event.py` can be imported as a module. It contains two functions useful
for writing generators:
* `read_csv(csv_path, selector=(0, 1))` - Returns the contents of a CSV
  file as list of tuples for easy processing.
* `make_event(records, programID, **kwargs)` - Turns a list of tuples into
  an openADR 3.1 compliant event structure.


## Deployment

Simply serve the `static_vtn/` directory from any HTTP server.


## Compatibility tested with:
* [OpenADR 3 VEN integration for Home Assistant](https://github.com/grid-coordination/openadr3-ven-hass)


## Requirements
* python 3.11 or higher


## References

- [OpenADR Alliance](https://www.openadr.org/)
- [openADR 3.0 Specification](https://www.openadr.org/openADR-30-Specification) - Also
  accessible without registration at
  [grid-coordination](https://github.com/grid-coordination/openadr3-specification).

