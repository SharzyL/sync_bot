import logging


def get_logger(name: str):
    log_fmt = logging.Formatter(
        f"%(asctime)s - %(levelname)s: {name}: %(message)s",
        "%Y %b %d %H:%M:%S"
    )
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(f'{name}.log', encoding='utf8')
    fh.setLevel(logging.INFO)
    fh.setFormatter(log_fmt)
    logger.addHandler(fh)
    return logger


def log_func(logger):
    """
    a decorator to log the function call
    :return: decorated function
    """
    def wrapper(func):
        def _format_arg(args, kwargs):
            return ', '.join(
                [str(arg) for arg in args]
                + [f'{key}={value}' for key, value in kwargs.items()]
            )

        def new_func(*args, **kwargs):
            try:
                # Because of logging work on gbk encoding by default...So we need some processing
                response = func(*args, **kwargs)
                logger.info('%s(%s)    %s', func.__name__, _format_arg(args, kwargs), str(response))
                return response
            except Exception as e:
                logger.error('%s(%s)    error: %s', func.__name__, _format_arg(args, kwargs), e)
                raise e

        return new_func

    return wrapper
