# -*- coding: utf-8 -*-

######
# 1C #
######

import cnf
import sc
from scripts_interface import c_admin_tasks_manager
from xml_synch import c_read_lists_from_1C_task, c_build_excessive_links

def main():
    load_file_dir = cnf.get_cnf_text("SynchData", "DirWith1Cdata")
    load_file_name = cnf.get_cnf_text("SynchData", "outxml_Counterparties")

    # Делаем админа
    logger = sc.build_synch_logger()
    mng = c_admin_tasks_manager()
    mng.set_log_to_logger(logger)

    # Формируем список задач
    mng.add_task(c_read_lists_from_1C_task(load_file_dir + load_file_name))
    mng.add_task(c_build_excessive_links())

    # Запускаем (запустятся в порядке добавления)
    mng.run_tasks()

if __name__ == "__main__":
    main()
