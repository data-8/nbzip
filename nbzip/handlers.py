from tornado import gen, web
from notebook.base.handlers import IPythonHandler

import os
import zipfile


class ZipStream(object):
    def __init__(self, handler):
        self.handler = handler
        self.position = 0

    def write(self, data):
        self.position += len(data)
        self.handler.write(data)

    def tell(self):
        return self.position

    def flush(self):
        self.handler.flush()


class ZipHandler(IPythonHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @web.authenticated
    @gen.coroutine
    def get(self):
        zip_path = self.get_argument('zipPath')
        zip_token = self.get_argument('zipToken')

        # We gonna send out event streams!
        self.set_header('content-type', 'application/octet-stream')
        self.set_header('cache-control', 'no-cache')
        self.set_header(
            'content-disposition',
            'attachment; filename=\"notebook-{}.zip\"'.format(zip_path)
        )

        if zip_path == '':
            zip_path = '.'

        self.log.info('zipping')

        file_name = None
        with zipfile.ZipFile(ZipStream(self), mode='w') as zf:
            for root, dirs, files in os.walk(zip_path):
                for file in files:
                    file_name = os.path.join(root, file)
                    self.log.info("{}\n".format(file_name))
                    zf.write(file_name, arcname=os.path.join(root[len(zip_path):], file))

        self.set_cookie("zipToken", zip_token)
        self.log.info('Finished zipping')
