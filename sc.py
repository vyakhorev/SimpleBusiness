# -*- coding: utf-8 -*-

import logging

def build_synch_logger():
    # Конфигурируем логгера (можно было своего не делать...)
    # https://docs.python.org/2/howto/logging-cookbook.html
    logger = logging.getLogger('sycnh_app')
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler('synch.log')
    fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger