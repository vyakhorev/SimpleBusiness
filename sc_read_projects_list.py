# -*- coding: utf-8 -*-

######
# 1C #
######

# А теперь работаем
import cnf
import sc
from scripts_interface import c_admin_tasks_manager
from xml_synch import c_read_dynamic_data_from_1C_task

def main():
    load_file_dir = cnf.get_cnf_text("SynchData", "DirWith1Cdata")
    load_file_name = cnf.get_cnf_text("SynchData", "outxml_ProjectsAndOrders")

    # Делаем админа
    logger = sc.build_synch_logger()
    mng = c_admin_tasks_manager()
    mng.set_log_to_logger(logger)

    # Формируем список задач
    mng.add_task(c_read_dynamic_data_from_1C_task(load_file_dir + load_file_name))

    # Запускаем (запустятся в порядке добавления)
    mng.run_tasks()


if __name__ == "__main__":
    main()
