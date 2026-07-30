# Pre-container scripts (not on any code path)

Everything in this directory, and in `../swat`, predates the containerised stack
and is **Python 2**. None of it parses under the Python 3 the project runs on:

    $ python3 -c "import ast; ast.parse(open('import_sample_data_wy.py').read())"
    SyntaxError: Missing parentheses in call to 'print'

Nothing references it. `install.sh` option 10 used to run
`import_sample_data_wy.py`, which meant that option could only ever fail; it now
runs `scripts/load_demo.py`, the same loader `make demo` uses. CI excludes both
directories from its byte-compile step for the same reason.

Kept for reference — the modern equivalents are:

| here | now |
|---|---|
| `import_sample_data*.py` | `scripts/load_demo.py` |
| `simple_http_server.py` | `tools/http_server.py` |
| `wps.py` | `tools/wpsserver/wpsprocess/invest_models.py` |
| `gs_example.py`, `test_invest_sdr_demo.py` | `scripts/run_model_jobs.py` |
