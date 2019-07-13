import json
import os

_CONFIG_PATH = 'bot.json'
_DEFAULT_CONFIG = {
    'token': '',
    'chat_id': 0,
    'offset': 0,
    'sync_paths': [],
    'sync_interval': 30,
}
_config_instance = {}


def write_config(_config) -> None:
    with open(_CONFIG_PATH, 'w') as fp:
        json.dump(_config, fp)


def _read_config() -> object:
    try:
        with open(_CONFIG_PATH, 'r') as fp:
            _config = json.load(fp)
        for key in _DEFAULT_CONFIG.keys():
            if key not in _config:
                raise json.JSONDecodeError
        return _config
    except FileNotFoundError:
        return _init_config()
    except json.JSONDecodeError:
        while True:
            re_init = input(f'{_CONFIG_PATH} in wrong format, re-initialize it? (y/n)')
            if re_init == 'y':
                return _init_config()
            elif re_init == 'n':
                return _init_config()


def _init_config() -> map:
    while True:
        _ = input('Edit config file interactively or in editor?(i/e)\n')
        if _ == 'e':
            os.system(_CONFIG_PATH)
        elif _ == 'i':
            break
        else:
            input('Illegal character')
            continue
    _config = _DEFAULT_CONFIG.copy()
    _config['token'] = input('Enter your bot token:\n')
    _paths = []
    while True:
        _paths.append(input('Enter a path to be synced:\n'))
        _ = input('anymore?(y/n)\n')
        if _ == 'y':
            continue
        else:
            break
    _config['sync_paths'] = _paths
    write_config(_config)
    return _config


def get_config() -> map:
    global _config_instance
    if _config_instance:
        return _config_instance
    else:
        _config_instance = _read_config()
        return _config_instance


if __name__ == '__main__':
    get_config()
