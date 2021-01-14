"""
基于pymysql封装的ORM
原因：
1. 装饰器中使用了锁来保证多线程并发也不会生成多个实例，使用singleton装饰的类都可以保证全局只存在一个实例
2. mysql_cursor利用了with的上下文管理机制，简化了数据库连接的手动关闭操作
"""
from datetime import datetime

from backend.conf import MYSQL_CONF
import logging
import threading
from contextlib import contextmanager

import pymysql
from pymysql import MySQLError
from backend.utils import snake_to_camel


# singleton pattern
def singleton(cls):
    instance_store = {}

    def wrap(*args, **kwargs):
        if cls not in instance_store:
            with cls._instance_lock:
                if cls not in instance_store:
                    ins = cls(*args, **kwargs)
                    instance_store[cls] = ins
        return instance_store[cls]

    return wrap


def _parse_execute_sql(sql):
    sql = sql.lstrip()
    cmd = sql.split(' ', 1)[0].lower()
    return cmd


class AbstractSQLClient(object):

    def __init__(self, host, user, password, db, port, debug=False):
        self.host = host
        self.user = user
        self.password = password
        self.db = db
        self.port = port
        self.thread_local = threading.local()
        self.debug = debug

    @contextmanager
    def mysql_cursor(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
        except MySQLError as e:
            logging.info("获取mysql cursor失败：{}".format(e))
            raise MySQLError(e)
        finally:
            conn.commit()
            cursor.close()
            conn.close()

    def get_connection(self):
        raise NotImplementedError

    def execute(self, sql, *args, batch=False, debug=False):
        cmd = _parse_execute_sql(sql)
        with self.mysql_cursor() as cursor:
            if self.debug or debug:
                print('DebugSQL:', cursor.mogrify(sql, args))
            result = cursor.execute(sql, args)
            if cmd in ['select', 'show']:
                return cursor.fetchall()
            elif cmd == 'insert':
                if batch:
                    return range(cursor.lastrowid, cursor.lastrowid + cursor.rowcount)
                return cursor.lastrowid
            return result


@singleton
class SQLClient(AbstractSQLClient):
    _instance_lock = threading.Lock()

    def get_connection(self):
        conn = getattr(self.thread_local, 'connection', None)
        if not conn:
            conn = pymysql.connect(
                host=self.host,
                user=self.user,
                passwd=self.password,
                db=self.db,
                port=int(self.port),
                charset='utf8mb4',
                autocommit=True
            )
            print("重新赋值conn")
            self.thread_local.connection = conn
        conn.ping(True)
        return conn


class BaseModel(object):
    """
    The base class of entity model
    """
    table = NotImplemented
    fields = []
    mc_key = "%s:memory_cache_key"
    mc_key_version = "v1"
    _instance_lock = threading.Lock()  # 单例模式使用

    def __init__(self, *args, **kwargs):
        index = 0
        amount = len(args)
        for field in self.fields:
            if field in kwargs:
                value = kwargs[field]
            # pretend from indexError
            elif index > amount:
                continue
            else:
                value = args[index]
            setattr(self, field, value)
            index += 1

    def __hash__(self):
        return hash((self.__class__, self.id))

    @classmethod
    def _joined_fields(cls):
        if not hasattr(cls, '__joined_fields'):
            cls.__join_fields = ','.join(
                ['`' + field + '`' for field in cls.fields])
        return cls.__join_fields

    @classmethod
    def get(cls, id, force=False):
        rs = store.execute(
            'select {0} from {1} '
            'where id=%s'.format(cls._joined_fields(), cls.table), id)
        return cls(*rs[0]) if rs else ''

    @classmethod
    def add(cls, *args, **kwargs):
        idx = 0
        input_fields_format = []
        input_fields = []
        values = []
        for field in cls.fields:
            if field in kwargs:
                value = kwargs[field]
            elif field == 'id':
                continue
            elif idx < len(args):
                value = args[idx]
                idx += 1
            else:
                continue
            input_fields.append(field)
            if field == 'update_time' or field == 'create_time':
                input_fields_format.append('now()')
            else:
                input_fields_format.append('%s')
                values.append(value)

        input_fields = ['`' + field + '`' for field in input_fields]
        sql = "insert into {0} ({1}) values({2})".format(
            cls.table, ','.join(input_fields), ','.join(input_fields_format))
        _id = store.execute(sql, *values)
        if _id:
            entity = cls.get(_id, force=True)
            return entity

    @classmethod
    def delete(cls, id):
        entity = cls.get(id)
        if not entity:
            return
        rs = store.execute(
            'delete from {0} where id=%s'
                .format(cls.table), id)
        return rs

    @classmethod
    def update(cls, id, **kwargs):
        rs = cls._update_store(id, **kwargs)
        entity = cls.get(id, force=True)
        return rs

    @classmethod
    def _update_store(cls, id, **kwargs):
        update_fields = []
        values = []
        for field in cls.fields:
            if field in kwargs:
                if field == 'update_time':
                    update_fields.append('`{}`=%s'.format(field))
                    values.append(datetime.now())
                else:
                    update_fields.append('`{}`=%s'.format(field))
                    values.append(kwargs[field])
        values.append(id)
        sql = 'update {0} set {1} where id = %s'.format(cls.table,
                                                        ','.join(update_fields))
        rs = store.execute(sql, *values)
        return rs

    @classmethod
    def gets(cls, ids, filter_none=False):
        cls.get_multi_by_mc(ids)
        objs = [cls.get(i) for i in ids]
        if filter_none:
            objs = list(filter(None, objs))
        return objs

    def save(self):
        d = {}
        if not hasattr(self, 'id') or not self.id:
            for field in self.fields:
                if field != 'id' and hasattr(self, field):
                    d[field] = getattr(self, field)
            entity = self.add(**d)
            self.id = entity.id
        else:
            updated_fields = {field: getattr(self, field) for field in self.fields
                              if field != 'id' and hasattr(self, field)}
            if not updated_fields:
                return self
            self._update_store(self.id, **updated_fields)
            entity = self.get(self.id)
        return entity

    @classmethod
    def scan(cls, conditions='', start=0, limit=None, step=100, default_index='primary'):
        cnt = 0
        sql = "select id from {0} use index ({1}) where id > %s {2} order by id limit '%s'".format(
            cls.table, default_index, conditions
        )
        count = 0
        while True if limit is None else count < limit:
            num = step if limit is None else min(limit - count, step)
            rs = store.execute(sql, start, num)
            ids = [r[0] for r in rs]
            if not ids:
                return

            for _id in ids:
                yield _id

            count += step
            start = ids[-1]

    def to_base_dict(self, *args, **kwargs):
        full = self.__dict__
        result = {}
        for field in self.fields:
            field = field.strip('`')
            if field in full:
                camel_case_key = self._camel_case_fields()[field]
                result[camel_case_key] = self._encode_value(full[field])
        return result

    @classmethod
    def _camel_case_fields(cls):
        """
        :return: dict
        """
        if not hasattr(cls, '__camel_case_fields'):
            cls.__camel_case_fields = {
                key: snake_to_camel(key) for key in
                cls.fields}
        return cls.__camel_case_fields


store = None


def make_store():
    global store
    store = SQLClient(MYSQL_CONF['host'], MYSQL_CONF['user'], MYSQL_CONF['password'],
                      MYSQL_CONF['db'], MYSQL_CONF['port'])


def init_store():
    global store
    if store:
        return
    make_store()
