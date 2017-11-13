# nbzip
Zips and downloads all the contents of a jupyter notebook

![nbzip demo](doc/demo.gif)

# Installation

There is no package on PyPI available right now. You can install directly from master:

    pip install git+https://github.com/data-8/nbzip


You can then enable the serverextension

    jupyter serverextension enable --py nbzip --sys-prefix
    jupyter nbextension install --py nbzip
    jupyter nbextension enable --py nbzip

# What is it?

nbzip allows you to download all the contents of your jupyter notebook into a zipped file called 'notebook.zip'.
