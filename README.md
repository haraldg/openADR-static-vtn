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
├── httpd/                   # Files supporting the proper configuration of HTTP servers
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

Serve the `static_vtn/` directory from any HTTP server.

### lighttpd
For a simple setup without virtual hosts:
* Edit `/etc/lighttpd/lighttpd.conf` and set `server.document-root`
  to the proper directory.
* Copy `httpd/lighttpd.conf` to `/etc/lighttpd/conf-enabled/99_openADR.conf`,
  then edit it to replace `PATH_TO_REPO` with the actual path to the
  repository on your system.

**Optional:** To comply with the specification, you need to set up TLS
certificates. However, many VENs and the API check below work fine over
unencrypted HTTP.


## Testing your setup
Setting up the VTN as described above involves editing files by hand, and
mistakes are easy to make, especially in the `program` objects. It's therefore
a good idea to run an end-to-end check.

Requirements:

* The [OpenADR spec](https://www.openadr.org/specification) as a YAML file.
  If you'd rather not register, there is a
  [copy on GitHub](https://github.com/grid-coordination/openadr3-specification).
* [`schemathesis`](https://schemathesis.readthedocs.io/), installed on a
  machine that can reach your server over HTTP. Many distributions don't
  package it, so you will probably need a tool like `pip` to install it.

Mark endpoints that are required but useless for non-authenticating
setups as forbidden:

```bash
cd static_vtn/
mkdir reports resources subscriptions vens
chmod a-rwx reports resources subscriptions vens
```

Run the tests with a command like this:

```bash
schemathesis run ../openADR/1_OpenADR_3.1.0_20250801.yaml \
  --url http://localhost/ \
  --include-method GET \
  --exclude-method TRACE \
  --exclude-checks unsupported_method
```

You might see some errors that are unavoidable with your HTTP server, or
with a static setup in general. You can safely ignore these.

You will also very likely see errors saying that unauthenticated access is
not allowed. These appear to be errors in the specification, since other
OpenADR documents explicitly describe this use case.

If you find errors caused by files (or missing files) from
this repository, feel free to open an
[issue or pull request on GitHub](https://github.com/haraldg/openADR-static-vtn/).


## Compatibility tested with:
* [OpenADR 3 VEN integration for Home Assistant](https://github.com/grid-coordination/openadr3-ven-hass)


## Requirements
* python 3.11 or higher


## References

- [Project page](https://github.com/haraldg/openADR-static-vtn/)
- [OpenADR Alliance](https://www.openadr.org/)
- [OpenADR 3.1 Specification](https://www.openadr.org/specification) - Also
  accessible without registration at
  [grid-coordination](https://github.com/grid-coordination/openadr3-specification).

