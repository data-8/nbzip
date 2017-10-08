import subprocess
import os
import time
import logging
import requests
import json
import zipfile
from nbzip.handlers import TEMP_ZIP_NAME


TIMEOUT = 10  # in seconds
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
    while ("localhost:8888" not in run_and_return("jupyter notebook list")):
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
    return open(file_name, "r").read()


def create_test_files(test_dir_name):
    os.makedirs(test_dir_name)
    os.chdir(test_dir_name)
    create_new_file("testfile1.txt", "1")
    os.makedirs("dir1")
    create_new_file("dir1/testfile2.txt", "2")
    create_new_file("dir1/testfile3.txt", "3")
    os.makedirs("dir1/dir2")
    create_new_file("dir1/dir2/testfile4.txt", "4")
    os.makedirs("dir1/dir3")
    create_new_file("dir1/dir3/testfile5.txt", "5")
    create_new_file("dir1/dir3/testfile6.txt", "6")
    os.makedirs("dir4")
    create_new_file("dir4/testfile7.txt", "7")
    create_new_file("dir4/testfile8.txt", "8")


def check_stream_output():
    expected_stream = iter([
        'data: {"output": "Removing old notebook.zip...\\n", "phase": "zipping"}',
        'data: {{"output": "{} does not exist!\\n", "phase": "zipping"}}'.format(TEMP_ZIP_NAME),
        'data: {"output": "Zipping files:\\n", "phase": "zipping"}',
        'data: {"output": "./testfile1.txt\\n", "phase": "zipping"}',
        'data: {"output": "./dir1/testfile2.txt\\n", "phase": "zipping"}',
        'data: {"output": "./dir1/testfile3.txt\\n", "phase": "zipping"}',
        'data: {"output": "./dir1/dir2/testfile4.txt\\n", "phase": "zipping"}',
        'data: {"output": "./dir1/dir3/testfile5.txt\\n", "phase": "zipping"}',
        'data: {"output": "./dir1/dir3/testfile6.txt\\n", "phase": "zipping"}',
        'data: {"output": "./dir4/testfile7.txt\\n", "phase": "zipping"}',
        'data: {"output": "./dir4/testfile8.txt\\n", "phase": "zipping"}',
        'data: {"phase": "finished", "redirect": "http://localhost:8888/tree"}'
    ])

    try:
        resp = requests.get(
            url="http://localhost:8888/zip-download/api",
            params={
                "baseUrl": "http://localhost:8888"
            },
            stream=True
        )
        for line in resp.iter_lines():
            if line != b'':
                assert standardize_json_output(line.decode('utf-8')) == standardize_json_output(next(expected_stream))
        try:
            next(expected_stream)
            raise AssertionError("The event stream is shorter than expected.")
        except StopIteration:
            logging.info("Entire event stream matched expected output! :)")
    except (StopIteration, AssertionError) as e:
        logging.error("Event stream does not match expected output!")
        raise e


def unzip_zipped_file(dir_name):
    zipped_file = zipfile.ZipFile(TEMP_ZIP_NAME, 'r')
    zipped_file.extractall(dir_name)
    zipped_file.close()


def check_zipped_file_contents():
    contents_dir_name = '{}.contents'.format(TEMP_ZIP_NAME)
    unzip_zipped_file(contents_dir_name)

    os.chdir(contents_dir_name)

    assert get_file_contents("testfile1.txt") == "1"
    assert get_file_contents("dir1/testfile2.txt") == "2"
    assert get_file_contents("dir1/testfile3.txt") == "3"
    assert get_file_contents("dir1/dir2/testfile4.txt") == "4"
    assert get_file_contents("dir1/dir3/testfile5.txt") == "5"
    assert get_file_contents("dir1/dir3/testfile6.txt") == "6"
    assert get_file_contents("dir4/testfile7.txt") == "7"
    assert get_file_contents("dir4/testfile8.txt") == "8"

    num_of_files = 0
    for root, dirs, files in os.walk('./'):
        for file in files:
            num_of_files += 1
    assert num_of_files == 8


def test_zip():
    run_and_log("jupyter serverextension enable --py nbzip")
    run_and_log("jupyter nbextension enable --py nbzip")

    create_test_files('testenv')

    os.system("jupyter-notebook --port=8888 --no-browser &")

    if (not wait_for_notebook_to_start()):
        return

    try:
        check_stream_output()
        check_zipped_file_contents()
    finally:
        logging.info("Shutting down notebook server...")
        os.system("jupyter notebook stop 8888")
