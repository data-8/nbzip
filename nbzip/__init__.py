from notebook.utils import url_path_join
from .handlers import ZipHandler


# Jupyter Extension points
def _jupyter_server_extension_paths():
    return [{
        'module': 'nbzip',
    }]


def _jupyter_nbextension_paths():
    return [{
        "section": "tree",
        "dest": "nbzip",
        "src": "static",
        "require": "nbzip/tree"
    }]


def load_jupyter_server_extension(nbapp):
    web_app = nbapp.web_app
    base_url = url_path_join(web_app.settings['base_url'], 'zip-download')
    handlers = [
        (base_url, ZipHandler)
    ]
    web_app.add_handlers('.*', handlers)
