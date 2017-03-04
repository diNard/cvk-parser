#!/usr/bin/python
# -*- coding: utf8 -*-

from pony.orm import Database, db_session, commit, sql_debug
import builtins
#sql_debug(True)
builtins.db = Database('mysql', host='0.0.0.0', user='user', passwd='xxxx', db='cvk', port=53306)
#builtins.db = Database('sqlite', 'cvk.db', create_db=True)

from parser.region import RegionParser
from parser.ovo import OvoParser
from parser.ovo_update import OvoUpdateParser
from parser.station import StationParser
from parser.address import AddressParser
from parser.bound import BoundParser
from models.region import Region
from models.ovo import Ovo
from models.station import Station
import time

# Generate migrations for loaded models
db.generate_mapping(create_tables=True)

# CONSTS
REGION_LIST_URL = 'http://www.cvk.gov.ua/pls/vnd2014/wp030?PT001F01=910'

def load_regions():
    RegionParser(REGION_LIST_URL).parse()

@db_session
def load_ovos():
    regions = Region.select(lambda c: c.processed == False)
    for region in regions:
        OvoParser(region.url, region=region).parse()
        commit()
        print("region:", region.id)
        time.sleep(2)

@db_session
def update_ovos():
    ovos = Ovo.select(lambda c: c.processed_update == False)
    for ovo in ovos:
        OvoUpdateParser(ovo.url, ovo=ovo).parse()
        commit()
        print("ovo update:", ovo.id)
        time.sleep(2)

@db_session
def load_stations():
    ovos = Ovo.select(lambda c: c.processed == False)
    for ovo in ovos:
        StationParser(ovo.get_stations_url(), ovo=ovo).parse()
        commit()
        print("ovo:", ovo.id)
        time.sleep(2)

@db_session
def _load_addresses():
    stations = Station.select(lambda c: c.processed_address == False)[0:100]
    for station in stations:
        AddressParser(None, station=station).parse()
    return len(stations)

def load_addresses():
    cnt = 1
    while cnt > 0:
        cnt = _load_addresses()

@db_session
def _load_bounds():
    stations = Station.select(lambda c: c.processed == False)[0:100]
    for station in stations:
        BoundParser(None, station=station).parse()
        commit()
    return len(stations)

def load_bounds():
    cnt = 1
    while cnt > 0:
        cnt = _load_bounds()

load_regions()
load_ovos()
update_ovos()
load_stations()
load_addresses()
load_bounds()
