# -*- coding: utf-8 -*-

from utils import c_msg, c_task

class c_progress_reporter(object):
    # Печатает лог синхронизации в консоль или в окно
    def __init__(self, window_to_print=None, logger=None):
        if logger is None and window_to_print is None:
            self.printer = c_console_printer()
        elif not logger is None:
            self.printer = c_logger_printer(logger)
        elif not window_to_print is None:
            self.printer = c_wnd_printer(window_to_print)

    def pr(self, text, level=0, color='b'):
        self.printer.pr(text, level, color)

class c_console_printer(object):
    def pr(self, text, level=0, color='b'):
        # color для оконного принтера
        s = "\t"*level + text
        print(s)

class c_logger_printer(object):
    def __init__(self, logger):
        self.logger = logger

    def pr(self, text, level=0, color='b'):
        self.logger.info(text)

class c_wnd_printer(object):
    def __init__(self, a_textEdit):
        self.txt_wdg = a_textEdit
        self.txt_wdg.setReadOnly(True)

    def pr(self, text, level=0, color='b'):
        s = "\t"*level + text
        self.txt_wdg.longText.append(s)

class Queue(object):  #Стащил с курса
    "A container with a first-in-first-out (FIFO) queuing policy."
    def __init__(self):
        self.list = []

    def push(self,item):
        "Enqueue the 'item' into the queue"
        self.list.insert(0,item)

    def pop(self):
        """
          Dequeue the earliest enqueued item still in the queue. This
          operation removes the item from the queue.
        """
        return self.list.pop()

    def isEmpty(self):
        "Returns true if the queue is empty"
        return len(self.list) == 0

class c_admin_tasks_manager(object):
    # Менеджер задач синхронизации с 1С, контактов,
    # иных регулярных задач. Потихоньку отполируем..
    def __init__(self):
        self.rpr = None
        self.set_log_to_console()
        #self.set_log_window()
        self.tasks = Queue()

    def set_log_window(self, a_window):
        self.rpr = c_progress_reporter(window_to_print=a_window)

    def set_log_to_console(self):
        self.rpr = c_progress_reporter()

    def set_log_to_logger(self, a_logger):
        self.rpr = c_progress_reporter(logger=a_logger)

    def add_task(self, a_task):
        self.tasks.push(a_task)

    def run_tasks(self):
        while not(self.tasks.isEmpty()):
            tsk_i = self.tasks.pop()
            for msg_i in tsk_i.run_task():
                # Do interactive thing and responses here
                self.rpr.pr(unicode(msg_i))

class c_basic_task(c_task):
    # Does a simple thing
    def __init__(self, name, callable):
        self.callable = callable
        self.name = name

    def run_task(self):
        # Change this to create different tasks.
        # Must communicate with the task manager
        yield c_msg(u"%s - старт"%(self.name))
        self.callable()
        yield c_msg(u"%s - успешно завершено"%(self.name))

