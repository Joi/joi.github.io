#!/usr/bin/env python

import sys
import datetime

# date format# Monday, October 19, 2020 at 12:38:42 AM

dt = datetime.datetime.strptime(str(sys.argv[1]), '%A, %B %d, %Y at %I:%M:%S %p').strftime('%Y%m%d')

print(dt)
