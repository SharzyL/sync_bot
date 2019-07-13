import logging

log_fmt = logging.Formatter(
    "%(asctime)s - %(levelname)s: %(message)s",
    "%Y %b %d %H:%M:%S"
)
logger = logging.getLogger("bot")
logger.setLevel(logging.INFO)
fh = logging.FileHandler('bot.log')
fh.setLevel(logging.INFO)
fh.setFormatter(log_fmt)
logger.addHandler(fh)


def log_func(func):
    """
    a decorator to log the function call, paramete
    :return: decorated function
    """
    def _format_arg(args, kwargs):
        return ', '.join(
            [str(arg) for arg in args]
            + [f'{key}={value}' for key, value in kwargs.items()]
        )

    def new_func(*args, **kwargs):
        try:
            # Because of logging work on gbk encoding by default...So we need some processing
            response = func(*args, **kwargs)
            # if return_json:
            #     response = json.dumps(response, indent=2)
            logger.info('%s(%s)\n%s', func.__name__, _format_arg(args, kwargs), response)
            return response
        except Exception as e:
            logger.error('%s(%s)\n    error: %s', func.__name__, _format_arg(args, kwargs), e)
            raise e
    return new_func
