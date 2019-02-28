# coding=utf-8

from __future__ import unicode_literals

import warnings

from orMysql.db import db
from orMysql.fields import StringFiled, BaseField
from utils import wrapper_str, Property


class Queryer(object):
    def __init__(self, cls):
        self.cls = cls
        self.sql = "SELECT %s FROM %s " % (",".join(self.fields), self.cls.__tablename__)

    @property
    def fields(self):
        return list(map(lambda x: wrapper_str(x.name, "`"), self.cls.__map__.itervalues()))

    def filter(self, *args, **kwargs):
        if len(args) > 0:
            self.sql += " WHERE " + " AND ".join(args)
        return self

    def all(self):
        result = db.session.select(self.sql)
        object_result = []
        for x in result:
            obj = {}
            for k, v in x.iteritems():
                obj[self.cls.__db_map__[k]] = v
            object_result.append(self.cls(**obj))
        return object_result

    def first(self):
        self.sql += " LIMIT 1"
        objects = self.all()
        if len(objects) <= 0:
            raise Exception("record not exist")
        return objects[0]

    def limit(self, limit):
        self.sql += " LIMIT %s" % limit
        return self

    def offset(self, offset):
        self.sql += " OFFSET %s" % offset
        return self

    def order_by(self, *attr):
        self.sql += " ORDER BY %s" % (",".join(map(lambda x: str(x), attr)))
        return self

    def __repr__(self):
        return self.sql

class MetaModel(type):
    def __new__(cls, name, bases, attrs):
        if "__tablename__" not in attrs or not attrs["__tablename__"]:
            attrs["__tablename__"] = name.lower()
        __map__ = {}
        # 数据库字段和model属性的映射
        __db_map__ = {}
        # 记录主键
        __primary_key__ = []
        for k, v in attrs.iteritems():
            if isinstance(v, BaseField):
                __map__[k] = v
                __db_map__[v.name] = k
                if v.primary_key:
                    __primary_key__.append(v.name)
        if name != 'Model' and not __primary_key__:
            raise Exception("A table should have at least a primary key")
        attrs["__map__"] = __map__
        attrs["__db_map__"] = __db_map__
        attrs["__primary_key__"] = __primary_key__
        return type.__new__(cls, name, bases, attrs)


class Dict_Mixin(object):
    """
    主要实现一些dict的特性
    """

    def __init__(self, **kwargs):
        self.__dict__['__table_field__'] = []
        for k, v in kwargs.iteritems():
            self.__dict__[k] = v
            self.__dict__['__table_field__'].append(k)

    def __getitem__(self, key):
        return self.__dict__[key]

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def keys(self):
        for x in self.__dict__["__table_field__"]:
            yield x


class Model(Dict_Mixin):
    __metaclass__ = MetaModel

    def __init__(self, **kwargs):
        super(Model, self).__init__(**kwargs)

    def __getattr__(self, key):
        return self[key]

    def __setattr__(self, key, value):
        self[key] = value

    @Property
    def query(self):
        return Queryer(self)

    @property
    def save(self):
        attr_map = {}
        for key in self.keys():
            try:
                attr_map[key] = self.__map__[key]
            except KeyError as e:
                msg = "{} has no a filed named {}".format(self.__tablename__, e)
                warnings.warn(msg, SyntaxWarning)
        fileds = []
        values = []
        for k, v in attr_map.iteritems():
            fileds.append(wrapper_str(self.__map__[k].name, "`"))
            values.append(v.connect_str(self[k]))
        sql = "INSERT INTO %s (%s) VALUES (%s) " % (
            self.__tablename__,
            ",".join(fileds),
            ",".join(values))
        return sql

    def update(self, **kwargs):
        updates = []
        for k, v in kwargs.iteritems():
            if k in self.__map__:
                updates.append(self.__map__[k].name + "=" + self.__map__[k].connect_str(v))
        if not updates:
            return False
        sql = "UPDATE %s SET %s WHERE " % (self.__tablename__, ",".join(updates))
        # 根据主键设置过滤条件
        wheres = []
        for key in self.__primary_key__:
            wheres.append(key + "=" + self.__map__[self.__db_map__[key]].connect_str(self[self.__db_map__[key]]))
        if not wheres:
            return False
        sql += " AND ".join(wheres)
        return db.session.update(sql)