import psycopg2
import urllib.request
from pathlib import Path
from PyQt5 import Qt

import sys,os
import struct


import time
from datetime import date,datetime
from operator import itemgetter

from subprocess import call

from PADCrawler import PADCrawler
import scrapy
from scrapy.crawler import CrawlerProcess


class NoDataException(Exception):
	pass
class notifier:
	
	weekly_events = []
	daily_events = []
	rush_event_remaining_time = []
	
	remaining_dailys = []
	def __init__(self):
		self.data()
		
		##TODO have this run in background (start process)
		while(True):
			try:
				if(len(self.weekly_events) == 0 or len(self.daily_events) == 0):
					raise NoDataException
			except NoDataException:
				app = Qt.QApplication(sys.argv)
				systemtray_icon = Qt.QSystemTrayIcon(app)
				systemtray_icon.show()
				systemtray_icon.showMessage("PADCrawler Error", "Web Crawler was unable to crawl http://pad.skyozora.com, please check connection with the web", 3)
				sys.exit(1)
			title = ""
			url = ""
			time = ""
			##print(self.daily_events)
			for element in self.daily_events:
				title = element[1]
				url = element[2]
				time = element[0]
				if(time == "Today"):
					file_name = url.split('/')[-1]
					file = Path("C:/Users/Che-Wei/Desktop/PAD Bubble Notifier/" + file_name)
					#print(file)
					if(not file.is_file()):
						urllib.request.urlretrieve(url, file_name)
					self.show(title, url, time,file)
				else:
					self.remaining_dailys.append(element)
			
			self.remaining_dailys.sort(key=lambda tup:tup[0])
			
			for remainings in self.remaining_dailys:
				title = remainings[1]
				url = remainings[2]
				time = remainings[0]
				file_name = url.split('/')[-1]
				file = Path("C:/Users/Che-Wei/Desktop/PAD Bubble Notifier/" + file_name)
				###PyQt5 NOTES
				###Until PyQt is fully updated to PyQt5.9, we should not download icon until then
				#print(file)
				##if(not file.is_file()):
					##urllib.request.urlretrieve(url, file_name)
				self.show(title, url, time,file)
			
			'''
			systemtray_icon = Qt.QSystemTrayIcon(app, Qt.QIcon('/path/to/image'))
			systemtray_icon.show()
			systemtray_icon.showMessage('Title', 'Content')
			'''
			
			##TODO
			if(len(self.remaining_dailys) == 0):
				self.update()
				self.data()
		
		
	
	def data(self):
		##connection with PostgreSQL 9##
		connection = None
		
		try:
			connection = psycopg2.connect("dbname='padevents' user = 'postgres' host ='localhost' password = '27141688'")
		except:
			print ("Unable to connect to database, check PostgreSQL")
			sys.exit(1)
		
		cur = connection.cursor()
		cur.execute("""SELECT * from weekly_events""")
		self.weekly_events = cur.fetchall()
		cur.execute("""SELECT * from daily_events""")
		self.daily_events = cur.fetchall()
		
		
		##Make sure database insert new/change data#
		connection.commit()
		
		##close connection and cursor with PostgreSQL##
		cur.close()
		connection.close()
	
	
	##TODO
	##FLIP ASIAN TIME ZONE TO EST (12 hours diff)
	def show(self, title, url, times, file_name):
		app = Qt.QApplication(sys.argv)
		systemtray_icon = Qt.QSystemTrayIcon(app)
		systemtray_icon.show()
		if(times == "Today"):
			##we show all 
			systemtray_icon.showMessage(title, times)
		else:
			##construct time object from @param:times
			current_local_time = time.strftime("%H:%M")
			##re-format time
			new_time = times
			##format of time
			FMT = "%H:%M"
			delta_time = datetime.strptime(new_time, FMT) - datetime.strptime(current_local_time, FMT)
			##43200 is 12 hours difference
			if(-3600.0<=delta_time.total_seconds()+43200<=0):
				systemtray_icon.showMessage(title, times)
			else:
				##sleep the program for remaining time
				print("SLEEPING")
				time.sleep(delta_time.total_seconds()+43200)
			
			
			
			
	def update(self):
		##do cmd execute with scrapy directory and following command "scrapy crawl PADCrawler"
		process = CrawlerProcess({
			"USER_AGENT": "Mozilla/4.0 (compatible;MSIE 7.0; Windows Nt 5.1"
		})
		process.crawl(PADCrawler)
		process.start()
		


process = CrawlerProcess({'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)'})
process.crawl(PADCrawler)
process.start()	
start = notifier()
'''
First
US/DS and Wifi signal flashes, online icon off
Then
Wifi signal off
Then US/DS signal off


'''
	
	
