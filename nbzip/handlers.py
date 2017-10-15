from tornado import gen
from notebook.utils import url_path_join
from notebook.base.handlers import IPythonHandler
from queue import Queue, Empty

import traceback
import threading
import os


import tarfile

TEMP_ZIP_NAME = 'notebook.tar.gz'


class ZipStream(object):
    def __init__(self, handler):
        self.handler = handler
        self.position = 0

    def write(self, data):
        self.position += len(data)
        self.handler.write(data)

    def tell(self):
        return self.position


class ZipHandler(IPythonHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _emit_progress(self, progress):
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
        else:
            self.emit({'output': progress, 'phase': 'zipping'})

    @gen.coroutine
    def emit(self, data):
        if type(data) is not str:
            if 'output' in data:
                self.log.info(data['output'].rstrip())
        else:
            self.log.info(data)

    @gen.coroutine
    def get(self):
        try:
            base_url = self.get_argument('baseUrl')
            zip_token = self.get_argument('zipToken')

            # We gonna send out event streams!
            self.set_header('content-type', 'application/octet-stream')
            self.set_header('cache-control', 'no-cache')
            self.set_header('content-disposition', 'attachment; filename=\"{}\"'.format(TEMP_ZIP_NAME))

            self.emit({'output': 'Zipping files:\n', 'phase': 'zipping'})

            q = Queue()

            def zip():
                try:
                    file_name = None
                    # zipf = zipfile.ZipFile(TEMP_ZIP_NAME, 'w', zipfile.ZIP_DEFLATED)
                    with tarfile.open(fileobj=ZipStream(self), mode='w:gz') as tar:
                        for root, dirs, files in os.walk('./'):
                            for file in files:
                                file_name = os.path.join(root, file)
                                if file_name == os.path.join("./", TEMP_ZIP_NAME):
                                    continue
                                q.put_nowait("{}\n".format(file_name))
                                tar.add(file_name)

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
                self._emit_progress(progress)

            self.set_cookie("zipToken", zip_token)
            self.emit({'phase': 'finished', 'redirect': url_path_join(base_url, 'tree')})
        except Exception as e:
            self._emit_progress(e)
