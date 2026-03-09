#!/bin/bash

# Create a virtual environment at the project root
python -m venv .venv
source .venv/bin/activate

cd src
unzip palabos-v2.2.1.zip

cd 2-phase_LBM/build
cmake ..
make -j 2

cd ../../1-phase_LBM/build
cmake ..
make -j 2

cd ../../..
pip install --upgrade pip setuptools
pip install .

echo ""
echo "Installation complete!"
echo "Activate the virtual environment before running simulations:"
echo "  source .venv/bin/activate"
