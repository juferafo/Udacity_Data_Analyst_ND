#!/usr/bin/env python

# This script creates the databases for the output csv files

import os
import sqlite3 as sq3
import csv
import pandas

# The schema of the database includes: 
#     nodes.csv
#     nodes_tags.csv,
#     ways.csv,
#     ways_tags.csv,
#     ways_nodes.csv
# The initial table names are dropped in order to avoid initialization errors
schema = '''
DROP TABLE IF EXISTS 'nodes';
DROP TABLE IF EXISTS 'nodes_tags';
DROP TABLE IF EXISTS 'ways';
DROP TABLE IF EXISTS 'ways_tags';
DROP TABLE IF EXISTS 'ways_nodes';

CREATE TABLE nodes (
    id INTEGER PRIMARY KEY NOT NULL,
    lat REAL,
    lon REAL,
    version INTEGER 
);

CREATE TABLE nodes_tags (
    id INTEGER,
    key TEXT,
    value TEXT,
    type TEXT,
    FOREIGN KEY (id) REFERENCES nodes(id)
);

CREATE TABLE ways (
    id INTEGER PRIMARY KEY NOT NULL,
    nodes INTEGER,
    version TEXT 
);

CREATE TABLE ways_tags (
    id INTEGER NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    type TEXT,
    FOREIGN KEY (id) REFERENCES ways(id)
);

CREATE TABLE ways_nodes (
    id INTEGER NOT NULL,
    node_id INTEGER NOT NULL,
    position INTEGER NOT NULL,
    FOREIGN KEY (id) REFERENCES ways(id),
    FOREIGN KEY (node_id) REFERENCES nodes(id)
);
'''

data_base = "Cambridge.db"
conn   = sq3.connect(data_base)
c = conn.cursor()

c.executescript(schema)

csv_files = ["nodes", "nodes_tags", "ways", "ways_tags", "ways_nodes"]
for fcsv in csv_files:
    df = pandas.read_csv(fcsv+".csv")
    df.to_sql(fcsv, conn, if_exists = "replace")
conn.commit()
conn.close()
