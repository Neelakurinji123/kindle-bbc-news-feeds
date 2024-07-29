#!/usr/bin/env python3
# encoding=utf-8
# -*- coding: utf-8 -*-

# Written by : krishna@hottunalabs.net
# Update     : 28 Jul 2024 

from astral.geocoder import database, lookup
from datetime import datetime, date
from astral.sun import sun

location = 'Tokyo'

city=lookup(location, database())
s = sun(city.observer, date=date.today())
now =datetime.now().timestamp()
a_day = 60 * 60 * 24
sunrise = s["sunrise"].timestamp()
sunset = s["sunset"].timestamp()

if sunrise > sunset:
    sunrise -= a_day

if not sunrise < now < sunset:
    print('night')
else:
    print('day')
