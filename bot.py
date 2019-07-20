import json

import requests

from log import *

PROXY = {'http': 'http://localhost:1080', 'https': 'http://localhost:1080'}


def pickle_bots(_bots):
    with open('bot.json', 'w') as fp:
        json.dump([bot.__dict__() for bot in _bots], fp, indent=2, ensure_ascii=False)


class BotError(Exception):
    pass


def bot_log(func):
    def new_func(self, *args, **kwargs):
        return log_func(self.logger)(func)(self, *args, **kwargs)

    return new_func


class Bot:
    def __init__(self, bot_info: dict, _logger=get_logger('bot')):
        self.logger = _logger
        self.offset = bot_info['offset']
        self.name = bot_info['name']
        self.token = bot_info['token']
        self.chats = bot_info['chats']

    def default_chat(self):
        try:
            return self.chats[0]
        except IndexError:
            _ = input('You have not add a chat to your bot yet, want to add one (y / n)\n')
            if _ == 'y':
                self.chats.append(add_chat_interactively(self))
                pickle_bots(bots)
            else:
                exit(1)

    @staticmethod
    def _bot_request(method: str, url: str, *args, return_type='json', **kwargs):
        """
        An encapsulation of request, including error handling, and no logging
        By default, the response is treated as json object
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

    def _bot_url(self, method: str):
        return f'https://api.telegram.org/bot{self.token}/{method}'

    def _file_url(self, file_path: str):
        return f'https://api.telegram.org/file/bot{self.token}/{file_path}'

    @bot_log
    def _get_file_path(self, file_id: int):
        params = {
            'file_id': file_id,
        }
        response = self._bot_request('get', self._bot_url('getFile'), proxies=PROXY, params=params)
        return response['result']['file_path']

    def get_chat_by_name(self, name: str) -> dict:
        try:
            return (chat for chat in self.chats if chat.name == name).send(None)
        except StopIteration:
            raise ValueError(f'Bot named {name} not found')

    @bot_log
    def get_update(self, offset: int = None, update_offset=True):
        """
        Fetch recent received messages by offset
        :return: an array of messages objects, each in shape of
                {'message_id': ..., 'from': {...}, 'chat': {...}, 'date': ..., 'text': '...'}
        """
        params = {
            'offset': offset or self.offset + 1,
        }
        new_msg = self._bot_request('get', self._bot_url('getUpdates'), params=params)['result']
        if new_msg and update_offset:
            self.offset = new_msg[-1]['update_id']
            pickle_bots(bots)
        return new_msg

    @bot_log
    def get_file(self, file_id: int, local_save_path=None):
        """
        :param file_id:
        :param local_save_path: if specified, save file to given path
        :return: raw data of file
        """
        file_path = self._get_file_path(file_id)
        file = self._bot_request('get', self._file_url(file_path), return_type='raw')
        if local_save_path:
            with open(local_save_path, 'wb') as fd:
                fd.write(file.content)
        return file.content

    @bot_log
    def send_text(self, text: str, **kwargs):
        if 'chat_id' not in kwargs:
            kwargs['chat_id'] = self.default_chat()['chat_id']
        kwargs['text'] = text
        return self._bot_request('get', self._bot_url('sendMessage'), params=kwargs)

    @bot_log
    def post_img(self, file_path: str, **kwargs):
        if 'chat_id' not in kwargs:
            kwargs['chat_id'] = self.default_chat()['chat_id']
        files = {'photo': open(file_path, 'rb')}
        return self._bot_request('post', self._bot_url('sendPhoto'), files=files, params=kwargs)

    @bot_log
    def post_file(self, file_path: str, **kwargs):
        if 'chat_id' not in kwargs:
            kwargs['chat_id'] = self.default_chat()['chat_id']
        files = {'document': open(file_path, 'rb')}
        return self._bot_request('post', self._bot_url('sendDocument'), files=files, params=kwargs)

    def __dict__(self):
        return {
            "name": self.name,
            "token": self.token,
            "offset": self.offset,
            "chats": self.chats
        }


def add_chat_interactively(bot) -> bool:
    input("""We will detect the last message sent to your bot, to add the chat it belongs to your bot.
If the last message is not sent by the chat you want to add now, send it a message.
When you fell ready, enter any key.
""")
    print("Fetching data from server, waiting...")
    try:
        msgs = bot.get_update(-1, update_offset=False)
    except BotError:
        print("Failed to fetch data from server, check your network connection")
        return False
    if not msgs:
        print("It seems the bot has received no message.")
        return False
    msg = msgs[-1]
    msg_type = [key for key in msg.keys() if key != "update_id"][0]
    chat_id = msg[msg_type]['chat']['id']
    chat_type = msg[msg_type]['chat']['type']
    user_name = msg[msg_type]['chat']['username']
    _ = input(f'We detected a {chat_type} chat named "{user_name}", sure to add it? (y / n)\n').lower()
    if _ == 'y':
        pickle_bots(bots)
        bot.chats.append({'name': user_name, 'chat_id': chat_id, 'type': chat_type})
        print("Adding chat successful")
        return True


def add_bot_interactively():
    print("Let's start add your bot to local storage.")
    while True:
        name = input("Tell me the name which you call your bot:\n")
        token = input("Please input your bot token: (type 'redo' to restart)\n")
        if token == 'redo':
            continue
        _bot = Bot({
            'offset': 0,
            'name': name,
            'token': token,
            'chats': []
        })
        print("Let's add some chats to your bots.\n")
        while True:
            ok = add_chat_interactively(_bot)
            prompt = 'Succeeded to add a chat. Any more? (y / n)\n' if ok else \
                'Failed to add a chat. Retry? (y / n) \n'
            _ = input(prompt)
            if _ == 'y':
                continue
            else:
                break
        print('Succeeded to add the bot')
        bots.append(_bot)
        break
    pickle_bots(bots)


def get_bot_by_name(name: str) -> Bot:
    try:
        return (bot for bot in bots if bot.name == name).send(None)
    except StopIteration:
        raise ValueError(f'Bot named {name} not found')


def get_bot() -> Bot:
    return bots[0]


bots = []
try:
    with open('bot.json', 'r') as _fp:
        bots = [Bot(bot) for bot in json.load(_fp)]
        if not bots:
            raise json.JSONDecodeError
except FileNotFoundError:
    add_bot_interactively()
except json.JSONDecodeError:
    add_bot_interactively()


if __name__ == '__main__':
    b = get_bot_by_name('BOT')
    b.send_text('可爱')
