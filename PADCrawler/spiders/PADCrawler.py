import scrapy
import psycopg2
from bs4 import BeautifulSoup

import time

import urllib.request

class Stop(Exception):
	pass

class PADCrawler(scrapy.Spider):

	name = 'PADCrawler'
	start_urls = ['http://pad.skyozora.com/']
	weekly_event_image_url = []
	Group_E_Number = None
	Group_E_Time = []
	all_group_daily_time = [] 	
	weekly_event_title = []  			##list[String]
	weekly_event = []
	daily_event = []	
	
	def parse(self, response):
                
		domain = 'http://pad.skyozora.com/'
		res = BeautifulSoup(response.body)
		
		weekly_event_search = False  		##boolean
		
		weekly_event_time = [] 				##list[String]
							##[{"time":String, "event_title":String}]
				##list[String]
		daily_event_time_search = False		##boolean
		
		
		##weekly event
		
		
		
		##filtering table
		try:
			for data in response.xpath("//tr/td/a"):
				line = data.xpath("text()").extract()
				for word in line:
					##print(word)
					if(daily_event_time_search):
						if(word == "(任務列表)"):
							daily_event_time_search = False
						else:
							word = word.strip()
							if(word):
								self.all_group_daily_time.append(word)
					else:
						if(word == "推文"):
							daily_event_time_search = True
						
					
					
					if(weekly_event_search):
						if(word == "地下城列表請按此"):
							weekly_event_search = False
						else:
							word = word.strip()
							if(not word or "部份寵物究極進化" in word):
								raise Stop
							##print (word)
							self.weekly_event_title.append(word)
					else:
						if(word == "寵物購入商店"):
							weekly_event_search = True
					
		except Stop:
			pass
		
		try:
			weekly_event_search = False
			for nodes in response.xpath("//tr/td[1]"):
				dates = nodes.xpath("text()").extract()
				for date in dates:
					
					if(weekly_event_search and date != "配信中"):
						date = date.strip()
						if(not date):
							raise Stop
						##print (date)
						weekly_event_time.append(date)
					else:
						if(date == "配信中"):
							weekly_event_search = True
					
		except Stop:
				pass
	
		##print(self.all_group_daily_time)
		self.parse_weekly_image_url(response)
		self.parse_group_time(response)
		self.daily_time_attachment(response)
		
		
		
		#------DONE END HERE--------
		
		##TODO: ready to insert into daily table
		
		
		
		
		title_length = len(self.weekly_event_title)
		time_temp_length = len(weekly_event_time)//2
		##diff = title_length - time_temp_length
		del self.weekly_event_title[time_temp_length:len(self.weekly_event_title)]
		
		
		pos_1 = 0
		pos_2 = 1
		
		
		##organize list into dictionary tuples so it works nicely with INSERT in PostgreSQL##
		for x in range(0, len(self.weekly_event_title)):
			time_temps = weekly_event_time[pos_1]+weekly_event_time[pos_2]
			titles = self.weekly_event_title[x]
			dict = {"time":time_temps, "event_title":titles, "url":self.weekly_event_image_url[x]}
			self.weekly_event.append(dict)
			pos_1+=2
			pos_2+=2
		
		
		self.weekly_event = tuple(self.weekly_event)
		
		
		self.database_connect(response)
		
	
	
	def parse_weekly_image_url(self,response):
		'''
		self.weekly_event_image_url = response.xpath("//*[@id='container']/div[2]/table[2]//@src")
		self.weekly_event_image_url = self.weekly_event_image_url.extract()
		del self.weekly_event_image_url[0: len(self.weekly_event_image_url)-len(self.weekly_event_title)]
		count = 0
		print(self.weekly_event_image_url)
		try:
			for url in self.weekly_event_image_url:
				if(not url.startswith("http://")):
					print(url)
					count+=1
				else:
					raise Stop
		except Stop:
			pass
		'''
		urls = response.xpath("//*[@id='container']/div[2]/table[2]//@src")
		urls = urls.extract()
		del urls[0: len(urls)-len(self.weekly_event_title)]
		for url in urls:
			if(not url.startswith("http://")):
				if(url.startswith("/")):
					self.weekly_event_image_url.append("http://pad.skyozora.com" + url)
				else:
					self.weekly_event_image_url.append("http://pad.skyozora.com/" + url)
			else:
				self.weekly_event_image_url.append(url)
		
	def parse_group_time(self, response):
		##Filtering time to GROUP E
		'''
		Group_A_Number = [0,5,10,15,20,25,30]
		Group_B_Number = [1,6,11,16,21,26,31]
		Group_C_Number = [2,7,12,17,22,27,32]
		Group_D_Number = [3,8,13,18,23,28,33]
		'''
		self.Group_E_Number = [4,9,14,19,24,29,34,39,44,49]
		
		
		for x in self.Group_E_Number:
			try:
				if("時" in self.all_group_daily_time[x]):
					print(self.all_group_daily_time)
					list_split = self.all_group_daily_time[x][:2]
					self.Group_E_Time.append(list_split + ":00")
				else:
					self.Group_E_Time.append(self.all_group_daily_time[x])
			except IndexError:
				pass
		
	def daily_time_attachment(self, response):
		temp =[]
		for title in response.xpath("//*[@id='container']/div[1]/table[2]//@title"):
			temp.append(title.extract())
		
		daily_title = []
		for element in temp:
			if(element not in daily_title):
				daily_title.append(element)
		
		daily_event_titleWithImageURL = []
		
		temp2 = []
		for url in response.xpath("//img[@class='i40']/@src"):
			temp2.append(url.extract())
		
		
		image_url = []
		for element in temp2:
			if(element not in image_url):
				if(not element.startswith("http://")):
					if(element.startswith("/")):
						image_url.append("http://pad.skyozora.com" + element)
					else:
						image_url.append("http://pad.skyozora.com/" + element)
				else:
					image_url.append(element)
		
		
		###for x in range(0, len(image_url)):
		###	if(not image_url[x].startswith("http://")):
		###		image_url[x] = "http://pad.skyozora.com" + image_url[x]
		
		
		##print(len(daily_title))
		##print(len(image_url))
		
		dec_y = len(self.Group_E_Time)
		pointer = 0
		
		for x in range(0, len(daily_title)):
			if(x+dec_y == len(daily_title)):
				event_dict = {
					"time":self.Group_E_Time[pointer],
					"event_title":daily_title[x],
					"url":image_url[x]
				}
				daily_event_titleWithImageURL.append(event_dict)
				pointer+=1
				dec_y-=1
			else:
				event_dict = {
					"time":"Today",
					"event_title":daily_title[x],
					"url":image_url[x]
				}
				daily_event_titleWithImageURL.append(event_dict)
			
		
		
		##print(daily_title)
		
						##list[{time:String,event_title:String,url:String}]
		
		##Remove duplicate
		##This is done since I only need Group E information
		for element in daily_event_titleWithImageURL:
			if(element not in self.daily_event):
				self.daily_event.append(element)
		##Remove duplicate done
	
	def database_connect(self, response):
		##connection with PostgreSQL 9##
		connection = None
		
		try:
			connection = psycopg2.connect("dbname='padevents' user = 'postgres' host ='localhost' password = '27141688'")
		except:
			print ("Unable to connect to database, check PostgreSQL")
			sys.exit(1)
		
		cur = connection.cursor()
		cur.execute("""DELETE FROM daily_events""")
		cur.execute("""DELETE FROM weekly_events""")
		cur.executemany("""INSERT INTO weekly_events(time, event_title, url) VALUES (%(time)s, %(event_title)s, %(url)s)""", self.weekly_event)
		cur.executemany("""INSERT INTO daily_events(time, event_title, url) VALUES (%(time)s, %(event_title)s, %(url)s)""", self.daily_event)
		cur.execute("""SELECT * from weekly_events""")
		##print(cur.fetchall())
		cur.execute("""SELECT * from daily_events""")
		##print(cur.fetchall())
		##Make sure database insert new/change data#
		
		connection.commit()
		
		##close connection with PostgreSQL##
		
		cur.close()
		connection.close()
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		