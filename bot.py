import requests
from log import log_func
import json

PROXY = {'http': 'http://localhost:1080', 'https': 'http://localhost:1080'}


def bot_url(method: str):
    return f'https://api.telegram.org/bot{bot["token"]}/{method}'


def file_url(file_path: str):
    return f'https://api.telegram.org/file/bot{bot["token"]}/{file_path}'


def get_config():
    _bot = dict()
    try:
        config = json.load(open('bot.json', 'r'))
        _bot['token'], _bot['chat_id'], _bot['offset'] = config['token'], config['chat_id'], config['offset']
        return _bot
    except FileNotFoundError:
        _bot['token'], _bot['chat_id'], _bot['offset'] = 0, 0, 0
        with open('bot.json', 'w') as fp:
            json.dump(_bot, fp)
        print('Please edit config file bot.json first')
        exit(1)
    except json.JSONDecodeError as e:
        print("Failed to decode bot.json", e)
        exit(1)


bot = get_config()


def write_config():
    with open('bot.json', 'w') as fp:
        json.dump(bot, fp, indent=2)


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
            raise BotError(f'{method} {url} not ok')
        return response
    if return_type == 'raw':
        return r.content
    if return_type == 'text':
        return r.content.decode()


@log_func
def get_update(offset: int = None):
    """
    Fetch recent received messages by offset
    :return: an array of messages objects, each in shape of
            {'message_id': ..., 'from': {...}, 'chat': {...}, 'date': ..., 'text': '...'}
    """
    params = {
        'offset': offset or bot['offset'] + 1,
    }
    new_msg = _bot_request('get', bot_url('getUpdates'), params=params)['result']
    if new_msg:
        bot['offset'] = new_msg[-1]['update_id']
    write_config()
    return new_msg


def _get_file_path(file_id: int):
    params = {
        'file_id': file_id,
    }
    response = _bot_request('get', bot_url('getFile'), proxies=PROXY, params=params)
    return response['result']['file_path']


@log_func
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


@log_func
def send_text(text: str, chat_id: int = bot['chat_id']):
    params = {
        'chat_id': chat_id,
        'text': text,
    }
    return _bot_request('get', bot_url('sendMessage'), params=params)


@log_func
def post_img(file_path: str, chat_id: str = bot['chat_id']):
    params = {'chat_id': chat_id}
    files = {'photo': open(file_path, 'rb')}
    return _bot_request('post', bot_url('sendPhoto'), files=files, params=params)


@log_func
def post_file(file_path: str, chat_id: str = bot['chat_id']):
    params = {'chat_id': chat_id}
    files = {'document': open(file_path, 'rb')}
    return _bot_request('post', bot_url('sendDocument'), files=files, params=params)


if __name__ == '__main__':
    post_file('test.png')
