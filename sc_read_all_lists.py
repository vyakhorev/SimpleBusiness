# -*- coding: utf-8 -*-

# call this from 1C


# А теперь работаем
import cnf
import sc
from scripts_interface import c_admin_tasks_manager
from xml_synch import c_read_lists_from_1C_task

def main():
    load_file_dir = cnf.get_cnf_text("SynchData", "DirWith1Cdata")
    # Для валюты и Payment Terms важна последовательность.
    # Хотя повторный запуск ошибку исправит..
    file_names = []
    file_names += [cnf.get_cnf_text("SynchData", "outxml_Currencies")]
    file_names += [cnf.get_cnf_text("SynchData", "outxml_PaymentTerms")]

    # А это можно в любой последовательности
    file_names += [cnf.get_cnf_text("SynchData", "outxml_Vaults")]
    file_names += [cnf.get_cnf_text("SynchData", "outxml_Items")]
    file_names += [cnf.get_cnf_text("SynchData", "outxml_Counterparties")]

    # Делаем админа
    logger = sc.build_synch_logger()
    mng = c_admin_tasks_manager()
    mng.set_log_to_logger(logger)

    # Формируем список задач
    for fn in file_names:
        mng.add_task(c_read_lists_from_1C_task(load_file_dir + fn))

    # Запускаем (запустятся в порядке добавления)
    mng.run_tasks()


if __name__ == "__main__":
    main()
