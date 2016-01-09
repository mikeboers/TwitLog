


class Column(object):

    def __init__(self, name=None):
        self.name = name
        self._getter = self._setter = self._deleter = None
        self._persist = self._restore = None

    def copy(self):
        copy = Column(self.name)
        copy._getter  = self._getter
        copy._persist = self._persist
        copy._restore = self._restore
        return copy

    def getter(self, func):
        self._getter = func
        return self

    def persist(self, func):
        self._persist = func
        return self

    def restore(self, func):
        self._restore = func
        return self

    def __get__(self, obj, cls):
        if self._getter:
            return self._getter(obj)
        try:
            return obj.__dict__[self.name]
        except KeyError:
            raise AttributeError(self.name)

    def __set__(self, obj, value):
        obj.__dict__[self.name] = value
        obj.is_dirty = True

    def __delete__(self, obj):
        raise RuntimeError("cannot delete DB columns")



class DBMetaclass(type):

    def __new__(cls, name, bases, attrs):

        table_name = attrs.get('__tablename__')

        # Collect existing columns from bases.
        columns = {}
        for base in reversed(bases):
            table_name = table_name or getattr(base, '__tablename__', None)
            for col in getattr(base, '__columns__', []):
                columns[col.name] = col.copy()

        # Collect new columns.
        for k, v in attrs.iteritems():

            # If this is now a property, but it was once a column, upgrade it
            # to a column.
            if isinstance(v, property):
                col = columns.get(k)
                if col:
                    col._getter = v.fget
                    if v.fset or v.fdel:
                        raise ValueError('cannot wrap properties with setters or deleters')
                    attrs[k] = col
                    v = col

            if isinstance(v, Column):
                v.name = v.name or k
                columns[v.name] = v

        attrs['__columns__'] = [v for _, v in sorted(columns.iteritems())]

        return super(DBMetaclass, cls).__new__(cls, name, bases, attrs)


class DBObject(object):

    __metaclass__ = DBMetaclass

    def __init__(self, *args, **kwargs):
        self.id = None
        self.is_dirty = True

    def _connect(self):
        return self.home.db.connect()

    def id_or_persist(self, *args, **kwargs):
        return self.id or self.persist_in_db(*args, **kwargs)

    def persist_in_db(self, con=None, force=False):

        if not self.is_dirty and not force:
            return self.id

        data = {}
        for col in self.__columns__:
            try:
                if col._persist:
                    data[col.name] = col._persist(self)
                elif col._getter:
                    data[col.name] = col._getter(self)
                else:
                    data[col.name] = self.__dict__[col.name]
            except KeyError:
                pass

        con = con or self._connect()
        if self.id:
            con.update(self.__tablename__, data, {'id': self.id})
        else:
            self.id = con.insert(self.__tablename__, data)
            log.debug('%s added to %s with ID %d' % (self.__class__.__name__, self.__tablename__, self.id))
        self.is_dirty = False

        return self.id

    def restore_from_row(self, row, ignore=None):
        
        try:
            if self.id and self.id != row['id']:
                log.warning('Restoring from a mismatched ID; %s %d != %d' % (self.__tablename__, self.id, row['id']))
            self.id = row['id']
        except KeyError:
            pass
        
        for col in self.__columns__:

            try:
                val = row[col.name]
            except KeyError:
                continue

            if ignore and col.name in ignore:
                continue

            if col._restore:
                col._restore(self, val)
            else:
                self.__dict__[col.name] = val


