from notebook.notebookapp import list_running_servers
import subprocess
import io
import os
import time
import logging
import json
import shutil
import urllib.request
import tarfile
import tempfile
import zipfile


TIMEOUT = 10  # in seconds
PORT = 18888
logging.getLogger().setLevel(logging.INFO)


def standardize_json_output(line):
    return sorted(json.loads(line[6:]))


def run_and_log(cmd):
    logging.info("\n> {}\n{}".format(
        cmd,
        subprocess.check_output(cmd.split()).decode('utf-8')
    ))


def run_and_return(cmd):
    return subprocess.check_output(cmd.split()).decode('utf-8')


def wait_for_notebook_to_start():
    wait_time = 0
    logging.info("waiting for notebook to start...")
    while ("localhost:{}".format(PORT) not in run_and_return("jupyter notebook list")):
        if (wait_time >= TIMEOUT):
            logging.info("Test timed out...")
            return False
        time.sleep(1)
        logging.info("waiting...")
        wait_time += 1
    logging.info("Server started!!!!")
    run_and_log("jupyter notebook list")
    return True


def create_new_file(file_name, content):
    with open(file_name, "w+") as file:
        file.write(content)


def get_file_contents(file_name):
    with open(file_name) as f:
        return f.read()


def create_test_files(test_dir_name):
    if os.path.exists(test_dir_name):
        shutil.rmtree(test_dir_name)
    os.makedirs(test_dir_name)
    create_new_file(os.path.join(test_dir_name, "testfile1.txt"), "1")
    os.makedirs(os.path.join(test_dir_name, "dir1"))
    create_new_file(os.path.join(test_dir_name, "dir1/testfile2.txt"), "2")
    create_new_file(os.path.join(test_dir_name, "dir1/testfile3.txt"), "3")
    os.makedirs(os.path.join(test_dir_name, "dir1/dir2"))
    create_new_file(os.path.join(test_dir_name, "dir1/dir2/testfile4.txt"), "4")
    os.makedirs(os.path.join(test_dir_name, "dir1/dir3"))
    create_new_file(os.path.join(test_dir_name, "dir1/dir3/testfile5.txt"), "5")
    create_new_file(os.path.join(test_dir_name, "dir1/dir3/testfile6.txt"), "6")
    os.makedirs(os.path.join(test_dir_name, "dir4"))
    create_new_file(os.path.join(test_dir_name, "dir4/testfile7.txt"), "7")
    create_new_file(os.path.join(test_dir_name, "dir4/testfile8.txt"), "8")


def download_zip_file(download_path, token, fmt):
    req = urllib.request.Request(
        "http://localhost:{}/zip-download?zipPath={}&zipToken=1&format={}".format(PORT, download_path, fmt),
        headers={
            'Authorization': 'Token {}'.format(token)
        }
    )
    return io.BytesIO(urllib.request.urlopen(req).read())


def fetch_and_unzip(dir_name, download_path, token, fmt):
    if os.path.exists(dir_name):
        shutil.rmtree(dir_name)
    if fmt == 'tar.gz':
        zip_file = tarfile.open(fileobj=download_zip_file(download_path, token, fmt), mode='r:gz')
    else:
        zip_file = zipfile.ZipFile(download_zip_file(download_path, token, fmt), mode='r')
    zip_file.extractall(dir_name)
    zip_file.close()


def check_zipped_file_contents(env_dir, download_path, token, fmt):
    if download_path == 'Home':
        download_path = ''
    download_path = os.path.join(env_dir, download_path)
    file_value_pairs = get_all_file_contents(download_path)

    with tempfile.TemporaryDirectory() as target_directory:
        fetch_and_unzip(target_directory, download_path, token, fmt)

        for pair in file_value_pairs:
            assert get_file_contents(os.path.join(target_directory, pair[0])) == pair[1]

        num_of_files = len(get_all_file_contents(target_directory))
        assert num_of_files == len(file_value_pairs)


def get_all_file_contents(dir):
    ret = []
    for root, dirs, files in os.walk(dir):
        for file in files:
            file_name = os.path.join(root, file)
            ret.append((os.path.join(root[len(dir):], file), get_file_contents(file_name)))
    return ret


def test_zip():
    run_and_log("jupyter serverextension enable --py nbzip")
    run_and_log("jupyter nbextension enable --py nbzip")

    source_directory = 'testenv'
    create_test_files(source_directory)

    os.system("jupyter-notebook --port={} --no-browser &".format(PORT))

    if (not wait_for_notebook_to_start()):
        assert False, "Notebook server failed to start"

    server = next(list_running_servers())
    token = server['token']

    try:
        for fmt in ('zip', 'tar.gz'):
            for path in ('Home', 'dir1/', 'dir1/dir2', 'dir1/dir3', 'dir4'):
                check_zipped_file_contents(source_directory, path, token, fmt)
    finally:
        logging.info("Shutting down notebook server...")
        os.system("jupyter notebook stop {}".format(PORT))
