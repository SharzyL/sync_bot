import requests

import init
from log import *

PROXY = {'http': 'http://localhost:1080', 'https': 'http://localhost:1080'}
config = init.get_config()
logger = get_logger('bot')


def bot_url(method: str):
    return f'https://api.telegram.org/bot{config["token"]}/{method}'


def file_url(file_path: str):
    return f'https://api.telegram.org/file/bot{config["token"]}/{file_path}'


class BotError(Exception):
    pass


def _bot_request(method: str, url: str, *args, return_type='json', **kwargs):
    """
    An encapsulation of request, including error handling
    :param method: post / get
    :param url: url
    :param args: requests args (directly passed to request.get() / request.post()
    :param return_type: json / raw / text
    :param kwargs: requests kwargs (directly passed to request.get() / request.post()
    :return: json by default
    """
    try:
        if method.lower() == 'get':
            r = requests.get(url, proxies=PROXY, *args, **kwargs)
        elif method.lower() == 'post':
            r = requests.post(url, proxies=PROXY, *args, **kwargs)
        else:
            raise BotError(f'{method} is not a legal request method')
    except requests.exceptions.ProxyError:
        raise BotError(f"Failed to connect proxy {PROXY}")

    if return_type == 'json':
        response = r.json()
        if not response['ok']:
            raise BotError(f'{method} {url} not ok', response)
        return response
    if return_type == 'raw':
        return r.content
    if return_type == 'text':
        return r.content.decode()


@log_func(logger)
def get_update(offset: int = None):
    """
    Fetch recent received messages by offset
    :return: an array of messages objects, each in shape of
            {'message_id': ..., 'from': {...}, 'chat': {...}, 'date': ..., 'text': '...'}
    """
    params = {
        'offset': offset or config['offset'] + 1,
    }
    new_msg = _bot_request('get', bot_url('getUpdates'), params=params)['result']
    if new_msg:
        config['offset'] = new_msg[-1]['update_id']
    init.write_config(config)
    return new_msg


def _get_file_path(file_id: int):
    params = {
        'file_id': file_id,
    }
    response = _bot_request('get', bot_url('getFile'), proxies=PROXY, params=params)
    return response['result']['file_path']


@log_func(logger)
def get_file(file_id: int, local_save_path=None):
    """
    :param file_id:
    :param local_save_path: if specified, save file to given path
    :return: raw data of file
    """
    file_path = _get_file_path(file_id)
    file = _bot_request('get', file_url(file_path), return_type='raw')
    if local_save_path:
        with open(local_save_path, 'wb') as fd:
            fd.write(file.content)
    return file.content


@log_func(logger)
def send_text(text: str, **kwargs):
    if 'chat_id' not in kwargs:
        kwargs['chat_id'] = config['chat_id']
    kwargs['text'] = text
    return _bot_request('get', bot_url('sendMessage'), params=kwargs)


@log_func(logger)
def post_img(file_path: str, **kwargs):
    if 'chat_id' not in kwargs:
        kwargs['chat_id'] = config['chat_id']
    files = {'photo': open(file_path, 'rb')}
    return _bot_request('post', bot_url('sendPhoto'), files=files, params=kwargs)


@log_func(logger)
def post_file(file_path: str, **kwargs):
    if 'chat_id' not in kwargs:
        kwargs['chat_id'] = config['chat_id']
    files = {'document': open(file_path, 'rb')}
    return _bot_request('post', bot_url('sendDocument'), files=files, params=kwargs)


def _init_chat_id(_config) -> None:
    """
    if config is not initialized with chat_id entry, interactively initialize it
    :param _config: a config object
    :return: None
    """
    while True:
        try:
            input('Send your bot any message to detect a chat, then press enter:\n')
            print('Waiting...')
            _config['chat_id'] = get_update(-1)[-1]['message']['chat']['id']
            break
        except IndexError:
            print('Not receiving any message')
            continue
    print('initialization ok')
    init.write_config(config)


if not config['chat_id']:
    _init_chat_id(config)

if __name__ == '__main__':
    pass
