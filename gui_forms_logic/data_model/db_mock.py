__author__ = 'User'
import random
cable_types = ['HV', 'LV', 'Waterproof', 'Fireproof']


class LazyDict(dict):
    """
        dict wrapper for database-like inhabits
        Not all base methods implemented
    """
    def __init__(self, final_dict):
        super(LazyDict, self).__init__()
        self.final_dict = final_dict
        self.lock = True

    def __setitem__(self, key, value):
        if self.lock:
            print Exception("Can't set value")
        else:
            dict.__setitem__(self, key, value)

    def __getitem__(self, key):
        try:
            value = dict.__getitem__(self.final_dict, key)
        except KeyError:
            raise Exception('dict hasnt got this key')
        return value

    def __iter__(self):
        return iter(self.final_dict)

    def __len__(self):
        return len(self.final_dict)

    def __contains__(self, key):
        return key in self.final_dict


class BaseItem(object):
    def __init__(self, value):
        self.value = value


class Cable(BaseItem):
    def __init__(self, name):
        super(Cable, self).__init__(name)
        self.name = name
        self.cbtype = None
        self.diameter = None

    def __repr__(self):
        return '{} cable '.format(self.name)

#
# class Prices(BaseItem):
#     def __init__(self, value):
#         super(Prices, self).__init__(value)
#         self.currency = None


class db_fake(object):
    """
        :attr table: table in RAM
        :attr table_fin: table in Base
        :return :self
    """
    def __init__(self):
        self.open = False
        # self.commit_queue = []
        self.table_fin = {}
        self.table = LazyDict(self.table_fin)

    def commit(self):
        for k, v in self.table.iteritems():
            self.table_fin[k] = v

    def opendb(self):
        self.open = True
        self.table.lock = False

    def closedb(self):
        self.open = False
        self.table.lock = True

    def __enter__(self):
        if self.open:
            return self
        else:
            raise BaseException('database needs to be open')

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.commit()
        self.closedb()


def db_filling_up(db, cables=None):
    """
        :param db: input database
        :return: db with filled table_fin
    """
    if cables is None:
        cables = ['ava', 'eva', 'dnerpostal', 'kwakwa', 'ololo', 'Kuybushevchgun']

    for cab in cables:
        a_cab = Cable(cab)
        a_cab.cbtype = random.choice(cable_types)
        a_cab.diameter = random.randint(10, 60)
        db.opendb()
        with db as db:
            db.table[a_cab] = [a_cab.cbtype, a_cab.diameter]


if __name__ == '__main__':
    a = db_fake()
    db_filling_up(a)
    # a.table[666] = 'Evil'

    for k, v in a.table_fin.iteritems():
        print k, v
