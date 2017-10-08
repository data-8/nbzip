import subprocess
import os
import time
import logging
import requests
import json
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


def test_zip():
    run_and_log("jupyter serverextension enable --py nbzip")
    run_and_log("jupyter nbextension enable --py nbzip")

    create_test_files('testenv')

    os.system("jupyter-notebook --port=8888 --no-browser &")

    if (not wait_for_notebook_to_start()):
        return

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
    finally:
        logging.info("Shutting down notebook server...")
        os.system("jupyter notebook stop 8888")
