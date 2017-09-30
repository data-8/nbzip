from tornado import gen, web, locks
import traceback
import urllib.parse

from notebook.utils import url_path_join
from notebook.base.handlers import IPythonHandler
import threading
import json
import os
from queue import Queue, Empty
import jinja2
import zipfile

class ZipHandler(IPythonHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @gen.coroutine
    def emit(self, data):
        if type(data) is not str:
            serialized_data = json.dumps(data)
            if 'output' in data:
                self.log.info(data['output'].rstrip())
        else:
            serialized_data = data
            self.log.info(data)
        self.write('data: {}\n\n'.format(serialized_data))
        yield self.flush()

    @gen.coroutine
    def get(self):
        try:
            base_url = self.get_argument('baseUrl')

            # We gonna send out event streams!
            self.set_header('content-type', 'text/event-stream')
            self.set_header('cache-control', 'no-cache')

            self.emit({'output': 'Zipping files:\n', 'phase': 'zipping'})

            q = Queue()
            def zip():
                try:
                    file_name = None
                    zipf = zipfile.ZipFile('notebook.zip', 'w', zipfile.ZIP_DEFLATED)
                    for root, dirs, files in os.walk('./'):
                        for file in files:
                            file_name = os.path.join(root, file)
                            q.put_nowait("{}\n".format(file_name))
                            zipf.write(file_name)
                    zipf.close()

                    # Sentinel when we're done
                    q.put_nowait(None)
                except Exception as e:
                    q.put_nowait(e)
                    raise e
            self.gp_thread = threading.Thread(target=zip)

            self.gp_thread.start()

            while True:
                try:
                    progress = q.get_nowait()
                except Empty:
                    yield gen.sleep(0.5)
                    continue
                if progress is None:
                    break
                if isinstance(progress, Exception):
                    self.emit({
                        'phase': 'error',
                        'message': str(progress),
                        'output': '\n'.join([
                            l.strip()
                            for l in traceback.format_exception(
                                type(progress), progress, progress.__traceback__
                            )
                        ])
                    })
                    return

                self.emit({'output': progress, 'phase': 'zipping'})

            self.emit({'phase': 'finished', 'redirect': url_path_join(base_url, 'tree')})
        except Exception as e:
            self.emit({
                'phase': 'error',
                'message': str(e),
                'output': '\n'.join([
                    l.strip()
                    for l in traceback.format_exception(
                        type(e), e, e.__traceback__
                    )
                ])
            })


class UIHandler(IPythonHandler):
    def initialize(self):
        super().initialize()
        # FIXME: Is this really the best way to use jinja2 here?
        # I can't seem to get the jinja2 env in the base handler to
        # actually load templates from arbitrary paths ugh.
        jinja2_env = self.settings['jinja2_env']
        jinja2_env.loader = jinja2.ChoiceLoader([
            jinja2_env.loader,
            jinja2.FileSystemLoader(
                os.path.join(os.path.dirname(__file__), 'templates')
            )
        ])

    @gen.coroutine
    def get(self):
        self.write(
            self.render_template(
                'status.html'
            ))
        self.flush()
