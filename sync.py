import hashlib
import json
import os
import pickle
from concurrent.futures import ThreadPoolExecutor, as_completed
from os.path import join
from threading import Lock
from time import sleep

import bot
from log import *


def init_config():
    _config = {}
    seconds = int(input('How many seconds between every sync check?\n'))
    chat_name = input('Which chat you want to sync to?\n')
    paths = []
    while True:
        path = input('Tell me a path you want to sync\n')
        paths.append(path)
        _ = input('any more? (y / n)\n')
        if _ == 'y':
            continue
        else:
            break
    return {'sync_interval': seconds, 'chat_name': chat_name, 'sync_paths': paths}


def pickle_config(config):
    with open('sync.json', 'w') as fp:
        json.dump(config, fp, indent=2)


logger = get_logger('sync')
try:
    with open('sync.json', 'r') as _fp:
        config = json.load(_fp)
except FileNotFoundError:
    config = init_config()
    pickle_config(config)

sync_bot = bot.get_bot()
sync_interval = config['sync_interval']
sync_paths = config['sync_paths']
SYNC_CACHE = []
pool = ThreadPoolExecutor(max_workers=5)
synced_files_md5 = set()
try:
    with open('synced', 'rb') as synced:
        synced_files_md5 = pickle.load(synced)
except FileNotFoundError:
    pass


def _pickle() -> None:
    with open('synced', 'wb') as fp:
        pickle.dump(synced_files_md5, fp)


def update() -> None:
    global SYNC_CACHE
    lock = Lock()

    def _hash(anything) -> bytes:
        """
        a encapsulation of md5 hash function
        :param anything: a string or byte
        :return: hash value in byte form
        """
        md5 = hashlib.md5()
        md5.update(str(anything).encode('utf-8'))
        return md5.digest()

    def _hash_file(file_path: str) -> bytes:
        with open(file_path, 'rb') as fp:
            return _hash(fp.read())

    def _post_file(file_path):
        """
        Wrapped version of bot.post_file()
        :return: hash of file if successful, otherwise None
        """
        _hash_val = _hash_file(file_path)
        if _hash_val not in synced_files_md5:
            try:
                sync_bot.post_file(file_path)
                logger.info('Succeeded to upload file %s', file_path)
                lock.acquire()
                synced_files_md5.add(_hash_val)
                lock.release()
            except bot.BotError:
                return None
        return _hash_val

    files = [join(path, file) for path in sync_paths for file in os.listdir(path)]
    if files == SYNC_CACHE:
        logger.info('%s :No update detected')
        return
    futures = {
        pool.submit(_post_file, file)
        for file in files
    }
    # block main thread until anything is ok
    error_cnt = 0  # record numbers of failed-to-synced files
    for future in as_completed(futures):
        hash_val = future.result()
        if not hash_val:
            error_cnt += 1
        else:
            synced_files_md5.add(hash_val)
    _pickle()
    if not error_cnt:
        SYNC_CACHE = files
        logger.info("Sync complete")
    else:
        logger.error("Sync not complete")


if __name__ == '__main__':
    while True:
        update()
        sleep(sync_interval)
