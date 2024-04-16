#!/usr/bin/env python3

#* CONFIGURATIONS
db_filepath  = "/home/ahmad/arch/anniversaries/anniversaries.db"
default_mode = 'column'
#****************

import sys
from argparse   import ArgumentParser
from shlex      import split as shplit
from subprocess import run as run_in_bash

"""
Default SQL:  'SELECT rowid, * FROM anniversaries '
$ anniversaries
(appends 'ORDER BY date ASC ' to default SQL)
$ anniversaries 12
(appends 'WHERE rowid = 12' to default SQL)
$ anniversaries --where who = Nabi
(appends everything after --where to default SQL AS IS)
$ anniversaries --sort +date -who
(appends to SQL: 'ORDER BY date ASC, who DESC')
$ anniversaries --add ('Joe', '2024-12-23', 'birthday', 'a note')
(INSERT INTO anniversaries VALUES ('Joe', '2024-12-23', 'birthday', 'a note'))
$ anniversaries 12 --mod date 2025-12-23
(UPDATE anniversaries SET date = 2025-12-23 WHERE rowid = 12)
$ anniversaries --del 12
(DELETE FROM anniversaries WHERE rowid = 12)
"""

def main(*args):
    # Parse command-line arguments
    parser = ArgumentParser(
        description='Manipulate anniversaries database',
        epilog='Text at the bottom of help (Modify with code bin/anni*)',
        prefix_chars='-+')
    parser.add_argument('id', nargs='?', default=None, type=int, help='Rowid for specific entry') # ? = 0 or 1    argument
    # DELETE
    parser.add_argument('--del','-d', nargs='?', dest='delete', help='Signals DELETE')
    # INSERT & UPDATE
    parser.add_argument('--add','-a', action='store_true', dest='insert', help='Signals INSERT')
    parser.add_argument('--mod','-m', action='store_true', dest='update', help='Signals UPDATE')
    parser.add_argument('--who',  const=None, help='Name for the anniversary')
    parser.add_argument('--date', const=None, help='Date for the anniversary')
    parser.add_argument('--type', const=None, help='Type for the anniversary')
    parser.add_argument('--note', const=None, help='Note for the anniversary')
    # WHERE
    parser.add_argument('--where','-w', nargs='+', help='WHERE clause for filtering')  # + = 1 or many arguments > list IF provided
    # def extend_where(args,Q): pass
    parser.add_argument('--or',  dest='_or',  nargs='+')
    parser.add_argument('--and', dest='_and', nargs='+')
    # def order       (args,Q): pass
    parser.add_argument('--ord','-o', action='store_true')
    #todo ORDER BY ROWID
    parser.add_argument('-who',  action='store_const', const='DESC', help='Name for the anniversary')
    parser.add_argument('-date', action='store_const', const='DESC', help='Date for the anniversary')
    parser.add_argument('-type', action='store_const', const='DESC', help='Type for the anniversary')
    parser.add_argument('-note', action='store_const', const='DESC', help='Note for the anniversary')
    #todo parser ORDER BY ROWID
    parser.add_argument('+who',  action='store_const', const='ASC', help='Name for the anniversary')
    parser.add_argument('+date', action='store_const', const='ASC', help='Date for the anniversary')
    parser.add_argument('+type', action='store_const', const='ASC', help='Type for the anniversary')
    parser.add_argument('+note', action='store_const', const='ASC', help='Note for the anniversary')
    # def limit       (args,Q): pass
    parser.add_argument('--lim','-l')
    parser.add_argument('--ofs', dest='offset')
    # For more complex queries
    parser.add_argument('--sql', nargs='*', help='Should execute passed queries as they are')

    # Parse arguments and execute corresponding SQL queries
    #^ Testing only
    #* args = parser.parse_args(shplit(""))
    #* args = parser.parse_args(shplit("12"))
    #* args = parser.parse_args(shplit("--add --who ahmad --date 2024-12-03 --type birthday --note 'a lil note'"))
    #* args = parser.parse_args(shplit("--add --who ahmad --date 2024-12-03"))
    #! args = parser.parse_args(shplit("--add ahmad 2024-12-03")) failed test
    #* args = parser.parse_args(shplit("37 --mod --note 2024-12-23"))
    #* args = parser.parse_args(shplit("24 --mod --who updated --date updated --type updated --note 'sdf sdf sdf sdf sdf sdf sdf sdf '"))
    #* args = parser.parse_args(shplit("--del 23"))
    #* args = parser.parse_args(shplit("--where who = Nabi"))
    #! args = parser.parse_args(shplit("--where rowid <= 20")) #todo need quotes
    #* args = parser.parse_args(shplit("--where type LIKE b%"))
    #* args = parser.parse_args(shplit("--where who = Nabi --and type = marriage"))
    #* args = parser.parse_args(shplit("--where who = Nabi --or type = marriage"))
    #* args = parser.parse_args(shplit("--ord -who +date -type +note"))
    #* args = parser.parse_args(shplit("--lim 3"))
    #* args = parser.parse_args(shplit("--lim 3 --ofs 4"))
    #^ Testing only

    args = parser.parse_args() #todo deactivate when testing
    Q = Query()

    if not args:
        print("\033[31mERROR\033[0m")
        sys.exit()
    elif args.insert:
        Q = insert(args)
    elif args.id:
        Q = update(args) if args.update else select_by_id(args.id)
    elif args.delete:
        Q = delete(args.delete)
    elif args.lim:
        Q.sortable = True
        Q = limit(args,Q)
    elif args.ord:
        Q = order(args,Q)
        if args.lim: Q = limit(args,Q)
    elif args.where:
        Q = where(args,Q)
        if args._and or args._or: Q = extend_where(args,Q)
        if args.ord: Q = order(args,Q)
        if args.lim: Q = limit(args,Q)
    elif args.sql:
        Q = Query(args.sql)
    else:
        Q = select_all()
    
    Q = sort_by_date(Q) # sorts by date if not already sorted

    # Final command
    command = f"sqlite3 -batch {db_filepath} \".mode {Q.mode}\" \"{Q.sql}\""
    # Execute
    run(command)
    # Print message if any
    if Q.msg: print(Q.msg)

#~ Functions definitions

class Query:
    def __init__(self, sql="SELECT rowid, * FROM anniversaries ", sortable=False, mode=default_mode, message=None):
        self.sql: str = sql
        self.sortable: bool = sortable
        self.mode: str = mode
        self.msg: str = message

def select_all():
    sql = "SELECT rowid, * FROM anniversaries; SELECT COUNT(*) AS 'rows' FROM anniversaries;"
    return Query(sql,True)

def select_by_id(_id):
    return Query(
        sql=f"SELECT rowid, * FROM anniversaries WHERE rowid = {_id} ",
        sortable=True,
        mode='line')

def insert(args):
    who  = f"'{args.who }'" if args.who  else 'NULL'
    date = f"'{args.date}'" if args.date else 'NULL'
    typ  = f"'{args.type}'" if args.type else 'NULL'
    note = f"'{args.note}'" if args.note else 'NULL'
    sql  = f"INSERT INTO anniversaries VALUES ({who},{date},{typ},{note});"
    sql += f"SELECT last_insert_rowid() AS 'Successfully inserted row';"
    mode = 'line'
    return Query(sql,False,mode)

def update(args):
    columns = ['who', 'date', 'type', 'note']
    values  = [args.who, args.date, args.type, args.note]
    stmts = []

    for i in range(4):
        if values[i]: stmts += [f"{columns[i]} = '{values[i]}'"]

    return Query(sql=f"UPDATE anniversaries SET {','.join(stmts)} WHERE rowid = {args.id}; SELECT changes() AS 'Number of rows updated'",
                 mode='line')

def delete(_id):
    return Query(sql=f"DELETE FROM anniversaries WHERE rowid = {_id}; SELECT changes() AS 'Number of rows deleted'",
                 mode='line')

def where(args,Q):
    cond = args.where
    Q.sql += f" WHERE {cond[0]} {cond[1]} '{cond[2]}'"
    Q.sortable = True
    return Q

def extend_where(args,Q):
    if args._and:
        Q.sql += f" AND {args._and[0]} {args._and[1]} '{args._and[2]}'"
    if args._or:
        Q.sql += f" OR {args._or[0]} {args._or[1]} '{args._or[2]}'"
    return Q

def order(args,Q):
    Q.sortable = False
    ordering_terms = []
    if args.who:  ordering_terms += [f"who {args.who}"]
    if args.date: ordering_terms += [f"date {args.date}"]
    if args.type: ordering_terms += [f"type {args.type}"]
    if args.note: ordering_terms += [f"note {args.note}"]
    if ordering_terms:
        Q.sql += "ORDER BY " + ", ".join(ordering_terms)
    return Q

def limit(args,Q):
    if Q.sortable:
        Q = sort_by_date(Q)
    Q.sql += f"LIMIT {args.lim}"
    if args.offset:
        Q.sql += f" OFFSET {args.offset}"
    return Q

def sort_by_date(Q):
    if Q.sortable:
        Q.sql += " ORDER BY date ASC "
        Q.sortable = False # to avoid adding ORDER BY twice
    return Q

def run(cmds):
    cmds = shplit(cmds)
    run_in_bash(cmds)

main(db_filepath,default_mode) # execute script after defining functions
