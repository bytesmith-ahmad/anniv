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
        epilog='Text at the bottom of help (Modify with code bin/anni*)')
    parser.add_argument('id', nargs='?', default=None, type=int, help='Rowid for specific entry') # ? = 0 or 1    argument
    parser.add_argument('--add','-a', action='store_true', dest='insert', help='Signals INSERT')
    parser.add_argument('--mod','-m', action='store_true', dest='update', help='Signals UPDATE')
    parser.add_argument('--del','-d', nargs='?', dest='delete', help='Signals DELETE')
    parser.add_argument('--who',  const=None, help='Name for the anniversary')
    parser.add_argument('--date', const=None, help='Date for the anniversary')
    parser.add_argument('--type', const=None, help='Type for the anniversary')
    parser.add_argument('--note', const=None, help='Note for the anniversary')
    parser.add_argument('--where','-w', nargs='+', help='WHERE clause for filtering')  # + = 1 or many arguments > list IF provided
    # def extend_where(args,Q): pass
    parser.add_argument('--or',  dest='_or',  nargs='+')
    parser.add_argument('--and', dest='_and', nargs='+')
    # def order       (args,Q): pass
    parser.add_argument('--ord','-o')
    # def limit       (args,Q): pass
    parser.add_argument('--lim','-l')

    # Parse arguments and execute corresponding SQL queries
    #^ Testing only
    args = parser.parse_args(shplit(""))
    #* args = parser.parse_args(shplit("12"))
    #* args = parser.parse_args(shplit("--add --who ahmad --date 2024-12-03 --type birthday --note 'a lil note'"))
    #* args = parser.parse_args(shplit("--add --who ahmad --date 2024-12-03"))
    #! args = parser.parse_args(shplit("--add ahmad 2024-12-03"))
    #* args = parser.parse_args(shplit("37 --mod --note 2025-12-23"))
    #* args = parser.parse_args(shplit("23 --mod --who updated --date updated --type updated --note 'sdf sdf sdf sdf sdf sdf sdf sdf '"))
    #* args = parser.parse_args(shplit("--del 23"))
    #* args = parser.parse_args(shplit("--where who = Nabi"))
    #* args = parser.parse_args(shplit("--where rowid <= 20"))
    #* args = parser.parse_args(shplit("--where type LIKE b%"))
    #args = parser.parse_args(shplit("--where who = ahmad --and type = marriage"))
    #! args = parser.parse_args(shplit("--where who = Nabi --or type = marriage"))
    #! args = parser.parse_args(shplit("--ord +date"))
    #! args = parser.parse_args(shplit("--ord -date --lim 3"))
    #! args = parser.parse_args(shplit("--lim 3"))
    #! args = parser.parse_args(shplit("--lim 3 --ofs 3"))
    #^ Testing only

    # args = parser.parse_args() #! activate when done
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
        Q = limit(args) # if no order take care of it
    elif args.ord:
        Q = order(args)
        if args.lim: Q = limit(args,Q)
    elif args.where:
        Q = where(args,Q)
        if args._and or args._or: Q = extend_where(args,Q)
        if args.ord: Q = order(args,Q)
        if args.lim: Q = limit(args,Q)
    else:
        Q = select_all()
    if not (args.ord or args.lim): Q = default_order(Q)

    # Final command
    command = f"sqlite3 -batch {db_filepath} \".mode {Q.mode}\" \"{Q.sql}\""
    # Execute
    run(command)
    # Print message if any
    if Q.msg: print(Q.msg)

#~ Functions definitions

class Query:
    def __init__(self, sql="SELECT rowid, * FROM anniversaries", mode=default_mode, message=None):
        self.sql: str = sql
        self.mode: str = mode
        self.msg: str = message

# Default SQL query
# select_clause = 'SELECT rowid, * FROM anniversaries '
# order_clause = 'ORDER BY date ASC'

def select_all():
    return Query()

def select_by_id(_id):
    return Query(f"SELECT rowid, * FROM anniversaries WHERE rowid = {_id} ",'line')

def insert(args):
    who  = f"'{args.who }'" if args.who  else 'NULL'
    date = f"'{args.date}'" if args.date else 'NULL'
    typ  = f"'{args.type}'" if args.type else 'NULL'
    note = f"'{args.note}'" if args.note else 'NULL'
    sql  = f"INSERT INTO anniversaries VALUES ({who},{date},{typ},{note});"
    sql += f"SELECT last_insert_rowid() AS 'Successfully created row';"
    mode = 'line'
    return Query(sql,mode)

def update(args):
    columns = ['who', 'date', 'type', 'note']
    values  = [args.who, args.date, args.type, args.note]
    stmts = []

    for i in range(4):
        if values[i]: stmts += [f"{columns[i]} = '{values[i]}'"]

    return Query(f"UPDATE anniversaries SET {','.join(stmts)} WHERE rowid = {args.id}; SELECT changes()", 'line')

def delete(_id):
    return Query(f"DELETE FROM anniversaries WHERE rowid = {_id}; SELECT changes()",'line')

def where(args,Q):
    sql = Q.sql
    cond = args.where
    sql += f" WHERE {cond[0]} {cond[1]} '{cond[2]}'"
    return Query(sql)

def extend_where(args,Q):
    if args._and:
        Q.sql += f" AND {args._and[0]} {args._and[1]} '{args._and[2]}'"
    if args._or:
        Q.sql += f" OR {args._or[0]} {args._or[1]} '{args._or[2]}'"
    return Q

def order       (args,Q): pass
def default_order(Q):
    Q.sql += " ORDER BY date ASC"
    return Q
def limit       (args,Q): pass
def run         (cmds,Q): pass
def run(cmds):
    cmds = shplit(cmds)
    run_in_bash(cmds)

main(db_filepath,default_mode) # execute script after defining functions
