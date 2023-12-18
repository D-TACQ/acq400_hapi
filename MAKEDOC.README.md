### Updating acq400_hapi documentation

Install dependencies:
```
    apt install python3-sphinx

    pip3 install sphinx-argparse
    pip3 install sphinx-design
    pip3 install sphinx-rtd-theme
```

Clone and Run:
```
    git clone https://github.com/sambelltacq/acq400_hapi_docs
    cd acq400_hapi_docs
    ./make_docs.sh
```

Push updated docs to master branch

```
    git add docs/
    git commit -m 'made from repo at commit <HASH>'
    git push
```