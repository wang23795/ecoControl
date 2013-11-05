#!/usr/bin/env python

# add system path
import sys
sys.path.insert(0, '..')

from optparse import OptionParser

from app import app, db
from models import *
from views import *
from crawler import *

if __name__ == '__main__':
	# setting up OptionParser for command line inputs
	parser = OptionParser() 
	parser.add_option("--with-crawler", action="store_true", dest="with_crawler", default=False, help="Enable crawler thread", metavar="CRAWLER") 
	(options, args) = parser.parse_args()
	
	if(options.with_crawler):
		#disable debug to avoid multiple threads
		app.config['DEBUG'] = False
		Crawler()

	app.run(host="0.0.0.0")