# -*- coding: utf-8 -*-

import db_main
import datetime

'''
Оценка скорости запросов (имитация работы интерфейса) для выгрузки заметок
'''


# Обвязка, используемая в main_gui
class cIteratorDispenser():
    '''
    Выдает содержимое итератора порциями. Можно потом усложнить до формирования нормальных запросов..
    '''
    def __init__(self, some_iterator):
        self.my_iterator = some_iterator
        self.finished = False

    def give_next(self, how_much=1):
        '''
        Args:
            how_much: сколько элементов хочется взять
        Returns: лист с элементами
        '''
        ans = []
        if self.finished: return ans
        for k in xrange(0,how_much):
            try:
                ans+=[next(self.my_iterator)]
            except StopIteration:
                self.finished = True
                return ans
        return ans

# Грузим первые и потом в цикле остальные, возвращая время
def scroll_test(Disp, HowManyPreLoad, HowManyPostLoad):
    postload_q_times = []
    rec_count = 0

    t0_1 = datetime.datetime.now()
    first_ones = Disp.give_next(HowManyPreLoad)
    t0_2 = datetime.datetime.now()
    preload_time = (t0_2-t0_1).microseconds
    rec_count += len(first_ones)
    while not Disp.finished:
        t1_1 = datetime.datetime.now()
        new_ones = Disp.give_next(HowManyPostLoad)
        t1_2 = datetime.datetime.now()
        postload_q_times.append((t1_2-t1_1).microseconds)
        rec_count += len(new_ones)

    av_postload = sum(postload_q_times)/len(postload_q_times)
    print("Preload %d ms., postload %d ms (loaded %d records)"% (preload_time, av_postload, rec_count))


# Тест!
TestRuns = 20

HowManyPreLoad = 5
HowManyPostLoad = 1

for x in range(0, TestRuns-1):
    the_dispenser = cIteratorDispenser(db_main.get_dynamic_crm_records_iterator())
    scroll_test(the_dispenser, HowManyPreLoad, HowManyPostLoad)


# db_main.get_dynamic_crm_records_iterator_v1()
#
# Preload 74000 ms., postload 5 ms (loaded 1452 records)
# Preload 100000 ms., postload 6 ms (loaded 1452 records)
# Preload 69000 ms., postload 5 ms (loaded 1452 records)
# Preload 68000 ms., postload 6 ms (loaded 1452 records)
# Preload 69000 ms., postload 7 ms (loaded 1452 records)
# Preload 68000 ms., postload 6 ms (loaded 1452 records)
# Preload 84000 ms., postload 6 ms (loaded 1452 records)
# Preload 100000 ms., postload 4 ms (loaded 1452 records)
# Preload 67000 ms., postload 6 ms (loaded 1452 records)
# Preload 69000 ms., postload 6 ms (loaded 1452 records)
# Preload 70000 ms., postload 5 ms (loaded 1452 records)
# Preload 67000 ms., postload 6 ms (loaded 1452 records)
# Preload 69000 ms., postload 7 ms (loaded 1452 records)
# Preload 66000 ms., postload 6 ms (loaded 1452 records)
# Preload 101000 ms., postload 7 ms (loaded 1452 records)
# Preload 74000 ms., postload 6 ms (loaded 1452 records)
# Preload 70000 ms., postload 6 ms (loaded 1452 records)
# Preload 67000 ms., postload 8 ms (loaded 1452 records)
# Preload 86000 ms., postload 5 ms (loaded 1452 records)

# db_main.get_dynamic_crm_records_iterator_v2()
#
# Preload 128000 ms., postload 6 ms (loaded 1452 records)
# Preload 147000 ms., postload 6 ms (loaded 1452 records)
# Preload 117000 ms., postload 8 ms (loaded 1452 records)
# Preload 116000 ms., postload 5 ms (loaded 1452 records)
# Preload 121000 ms., postload 5 ms (loaded 1452 records)
# Preload 117000 ms., postload 4 ms (loaded 1452 records)
# Preload 123000 ms., postload 4 ms (loaded 1452 records)
# Preload 149000 ms., postload 6 ms (loaded 1452 records)
# Preload 117000 ms., postload 6 ms (loaded 1452 records)
# Preload 119000 ms., postload 6 ms (loaded 1452 records)
# Preload 124000 ms., postload 5 ms (loaded 1452 records)
# Preload 117000 ms., postload 5 ms (loaded 1452 records)
# Preload 133000 ms., postload 6 ms (loaded 1452 records)
# Preload 128000 ms., postload 6 ms (loaded 1452 records)
# Preload 157000 ms., postload 4 ms (loaded 1452 records)
# Preload 116000 ms., postload 7 ms (loaded 1452 records)
# Preload 123000 ms., postload 7 ms (loaded 1452 records)
# Preload 125000 ms., postload 6 ms (loaded 1452 records)
# Preload 123000 ms., postload 7 ms (loaded 1452 records)

# db_main.get_dynamic_crm_records_iterator_v3()
# это гораздо лучше для GUI - осталось сортировку и фильтры сделать..

# Preload 5000 ms., postload 734 ms (loaded 1452 records)
# Preload 4000 ms., postload 714 ms (loaded 1452 records)
# Preload 4000 ms., postload 711 ms (loaded 1452 records)
# Preload 4000 ms., postload 705 ms (loaded 1452 records)
# Preload 4000 ms., postload 704 ms (loaded 1452 records)
# Preload 4000 ms., postload 700 ms (loaded 1452 records)
# Preload 4000 ms., postload 759 ms (loaded 1452 records)
# Preload 4000 ms., postload 704 ms (loaded 1452 records)
# Preload 4000 ms., postload 706 ms (loaded 1452 records)
# Preload 3000 ms., postload 727 ms (loaded 1452 records)
# Preload 3000 ms., postload 700 ms (loaded 1452 records)
# Preload 3000 ms., postload 714 ms (loaded 1452 records)
# Preload 4000 ms., postload 718 ms (loaded 1452 records)
# Preload 4000 ms., postload 712 ms (loaded 1452 records)
# Preload 3000 ms., postload 711 ms (loaded 1452 records)
# Preload 3000 ms., postload 754 ms (loaded 1452 records)
# Preload 4000 ms., postload 703 ms (loaded 1452 records)
# Preload 4000 ms., postload 711 ms (loaded 1452 records)
# Preload 3000 ms., postload 731 ms (loaded 1452 records)

# db_main.get_dynamic_crm_records_iterator_v4()
# С сортировкой по дате

# Preload 12000 ms., postload 600 ms (loaded 1452 records)
# Preload 7000 ms., postload 578 ms (loaded 1452 records)
# Preload 8000 ms., postload 591 ms (loaded 1452 records)
# Preload 8000 ms., postload 592 ms (loaded 1452 records)
# Preload 7000 ms., postload 587 ms (loaded 1452 records)
# Preload 7000 ms., postload 607 ms (loaded 1452 records)
# Preload 7000 ms., postload 608 ms (loaded 1452 records)
# Preload 7000 ms., postload 575 ms (loaded 1452 records)
# Preload 8000 ms., postload 578 ms (loaded 1452 records)
# Preload 8000 ms., postload 586 ms (loaded 1452 records)
# Preload 8000 ms., postload 574 ms (loaded 1452 records)
# Preload 7000 ms., postload 582 ms (loaded 1452 records)
# Preload 7000 ms., postload 575 ms (loaded 1452 records)
# Preload 8000 ms., postload 575 ms (loaded 1452 records)
# Preload 8000 ms., postload 582 ms (loaded 1452 records)
# Preload 8000 ms., postload 584 ms (loaded 1452 records)
# Preload 7000 ms., postload 577 ms (loaded 1452 records)
# Preload 7000 ms., postload 589 ms (loaded 1452 records)
# Preload 7000 ms., postload 575 ms (loaded 1452 records)