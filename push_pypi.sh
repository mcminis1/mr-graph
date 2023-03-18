#!/bin/bash

rm dist/mr_graph-*.tar.gz 
rm dist/mr_graph-*-py3-none-any.whl
python -m build --wheel .
python -m build --sdist .
twine upload dist/mr_graph-*.tar.gz dist/mr_graph-*-py3-none-any.whl --verbose
