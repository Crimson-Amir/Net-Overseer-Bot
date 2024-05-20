from psycopg2 import pool
from abc import ABC, abstractmethod


# Connection Section


class AccessDenied(Exception):
    def __init__(self, msg='You are not allowed'):
        super().__init__(msg)


class Singleton(type):
    _instance = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instance:
            cls._instance[cls] = super().__call__(*args, **kwargs)
        return cls._instance.get(cls)


class PostgresConnect(metaclass=Singleton):
    @staticmethod
    def connect(**kwargs):
        return pool.SimpleConnectionPool(1, 10, **kwargs)


class ConnectProxyDescriptor:
    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):
        return instance.__dict__.get(self.name)

    def __set__(self, instance, value):
        if self.name == 'db_port':
            if not isinstance(value, int):
                raise ValueError('db_port must be int')
        else:
            value = str(value)

        instance.__dict__[self.name] = value

    def __delete__(self, instance):
        raise AccessDenied()


class ConnectProxy:
    db_name = ConnectProxyDescriptor()
    db_host = ConnectProxyDescriptor()
    db_password = ConnectProxyDescriptor()
    db_port = ConnectProxyDescriptor()
    db_user = ConnectProxyDescriptor()

    def __init__(self, db_name, db_host, db_user, db_password, db_port : int):
        self.database = str(db_name)
        self.host = str(db_host)
        self.password = str(db_password)
        self.user = str(db_user)
        self.port = db_port

    def connect(self):
        return PostgresConnect().connect(**self.__dict__)


# Operation section


class AbstractFetch(ABC):
    def __init__(self, cursor, _size=2):
        self._cursor = cursor
        self._size = _size

    @abstractmethod
    def fetch(self):
        pass


class FetchAll(AbstractFetch):
    def fetch(self):
        return self._cursor.fetchall()


class FetchOne(AbstractFetch):
    def fetch(self):
        return self._cursor.fetchone()


class FetchMnay(AbstractFetch):
    def fetch(self):
        return self._cursor.fetchone(self._size)


class AbstractOperation(ABC):
    def __init__(self, connect, fetch=FetchAll, _fetch_size=2):
        self._connect = connect
        self._fetch = fetch
        self._fetch_size = _fetch_size

    @abstractmethod
    def execute(self, operations):
        pass

class QueryOperation(AbstractOperation):
    def execute(self, operations):
        with self._connect:
            with self._connect.cursor() as cursor:
                cursor.execute(operations['query'], operations.get('params'))
                return self._fetch(cursor, self._fetch_size).fetch()


class TransactionOperation(AbstractOperation):
    def execute(self, operations):
        try:
            with self._connect as connection:
                with self._connect.cursor() as cursor:
                    for _operation in [operations]:
                        cursor.execute(_operation['query'], _operation['params'])
                connection.commit()

        except Exception as e:
            print(e)
            self._connect.rollback()
            raise



def main():
    connect = ConnectProxy(db_name="my_shop",
                           db_host="localhost",
                           db_user="postgres",
                           db_password="amir1383amir",
                           db_port=2053).connect()

    for _ in range(12):
        create_con = connect.getconn()
        QueryOperation(create_con).execute({'query': "select * from user_detail"})
        connect.putconn(create_con)
        print(_)

    # a.execute({'query': "insert into user_detail (name) values (%s)", 'params': ('soka',)})
    # print(b)

main()

