conda env create -f environment.yaml

pip install --upgrade pip

pip install -q torch-scatter -f https://data.pyg.org/whl/torch-2.0.1+cu117.html

pip install -q torch-sparse -f https://data.pyg.org/whl/torch-2.0.1+cu117.html

pip install -q git+https://github.com/pyg-team/pytorch_geometric.git