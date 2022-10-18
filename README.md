# pyhemo (PYthonic HEad MOdeling)
**Python Interface to common BEM and FEM forward head modeling libraries**
<br>
[![build](https://github.com/harmening/pyhemo/actions/workflows/action.yml/badge.svg)](https://github.com/harmening/pyhemo/actions)
[![coverage](https://codecov.io/gh/harmening/pyhemo/branch/main/graph/badge.svg?token=LHJ5W57UE8)](https://codecov.io/gh/harmening/pyhemo)
[![python](https://img.shields.io/badge/python-3.6|3.7|3.8|3.9|3.10-blue.svg)](https://www.python.org/downloads/release/python-360/)



## Get up and running
### Prerequisites
- [Python3.6](https://www.python.org/downloads/) or newer
- [OpenMEEG](https://github.com/openmeeg/openmeeg/blob/master/README.rst#build-openmeeg-from-source) with python wrapping: compile with `"-DENABLE_PYTHON=ON"`
- [DUNEuro](https://gitlab.dune-project.org/duneuro/duneuro/-/wikis/installation-instructions) with its python bindings module [duneuro-py](https://gitlab.dune-project.org/duneuro/duneuro-py)

### Install pyhemo
```bash
git clone https://github.com/harmening/pyhemo
cd pyhemo
pip install -r requirements.txt
python setup.py install
```

### Run example BEM/FEM scripts:
```bash
$ python examples/comparison_bem_fem.py
```

## docker :whale:
The installation of all C-dependencies might be cumbersome. Therefore I suggest
using [pyhemos docker image](https://hub.docker.com/r/harmening/pyhemo), where
everything is installed and ready to use:
<!--- 
Pull pyhemo image from [docker hub](https://hub.docker.com/r/harmening/pyhemo):
--->
```bash
$ docker pull harmening/pyhemo
```
### Run example script interactively:
```bash
$ docker run -it harmening/pyhemo bash
$ python examples/comparison_bem_fem.py
```
or directly explore pyhemo via python prompt:
```bash
$ docker run -it harmening/pyhemo
$ import pyhemo
$ ...
```
<br>





## To Dos:
- Enable BEM/FEM usage alone without installing the other 
- Use [HArtMuT](https://github.com/harmening/HArtMuT) as standard/example head 
<!--- wie FEM hartmut bauen? colin mit ext
  nacken -> colinFEM ohne scalp. Dann extended scalp nehmen und drumpacken und
  FEM mesh erstellen)
--->
