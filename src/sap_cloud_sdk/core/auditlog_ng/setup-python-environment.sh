#!/bin/sh

echo "Setting up python environment"
echo "-----------------------------"
#
echo "(1) Setting up virtual environment"
python3 -m venv venv
echo "... done."
#
echo "(2) Activating virtual environment"
source ./venv/bin/activate
echo "... done."
#
echo "(3) Downloading dependencies"
pip install -r requirements-client.txt --extra-index-url https://buf.build/gen/python
echo "... done."