# -*- coding: utf-8 -*-

######
# 1C #
######

import cnf
import sc
from scripts_interface import c_admin_tasks_manager
from xml_synch import c_print_budget_to_csv

def main():
    print_file_dir = cnf.get_cnf_text("SynchData", "DirWithOutputData")
    print_file_name = cnf.get_cnf_text("SynchData", "FileForSalesBudgetExport")

    # Делаем админа
    logger = sc.build_synch_logger()
    mng = c_admin_tasks_manager()
    mng.set_log_to_logger(logger)

    # Формируем список задач
    mng.add_task(c_print_budget_to_csv(print_file_dir + print_file_name))

    # Запускаем (запустятся в порядке добавления)
    mng.run_tasks()

if __name__ == "__main__":
    main()