# -*- coding:utf-8 -*-
import MySQLdb

conn = MySQLdb.connect(
    host='localhost',
    port=3306,
    user='root',
    passwd='Eden@mysql',
    db='memeda',
    unix_socket='/tmp/mysql.sock',
)
cur = conn.cursor()

cur.execute('create table User(id char (50),nickname char(50),\
opponent char(50),energy int ,live bit , status int, behavior int, times int )')
#cur.execute('create table Ready(user_id char(50),id char(50),times int)')

cur.close()
conn.commit()
conn.close()
