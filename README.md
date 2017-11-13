# nbzip
Zips and downloads all the contents of a jupyter notebook

![nbzip demo](doc/demo.gif)

# Installation

    pip install nbzip

You can then enable the serverextension

    jupyter serverextension enable --py nbzip --sys-prefix
    jupyter nbextension install --py nbzip
    jupyter nbextension enable --py nbzip

# What is it?

nbzip allows you to download all the contents of your jupyter notebook into a zipped file called 'notebook.zip'.
