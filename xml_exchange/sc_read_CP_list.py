# -*- coding: utf-8 -*-

# Reads all lists from xml file
# call this from 1C

# Сначала сделаем рабочей директорией основную папку
import os
BASE_DIR = os.path.join(os.path.dirname(__file__), '..')
os.chdir(BASE_DIR)

# А теперь работаем
import cnf
from scripts_interface import c_admin_tasks_manager
from xml_synch import c_read_lists_from_1C_task
import logging

def main():
    load_file_dir = cnf.get_cnf_text("SynchData", "DirWith1Cdata")
    load_file_name = cnf.get_cnf_text("SynchData", "outxml_Counterparties")
    # Конфигурируем логгера (можно было своего не делать...)
    # https://docs.python.org/2/howto/logging-cookbook.html
    logger = logging.getLogger('sycnh_app')
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(r'.\xml_exchange\synch.log')
    fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(ch)

    # Делаем админа
    mng = c_admin_tasks_manager()
    mng.set_log_to_logger(logger)
    # Создаём очередь заданий (легко потом до сервера будет проапгрейдить)
    mng.add_task(c_read_lists_from_1C_task(load_file_dir + load_file_name))
    mng.run_tasks()

    # Побудем назойливыми и откроем лог в блокноте. Удобно, чё!
    os.startfile(r'.\xml_exchange\synch.log')

if __name__ == "__main__":
    main()
