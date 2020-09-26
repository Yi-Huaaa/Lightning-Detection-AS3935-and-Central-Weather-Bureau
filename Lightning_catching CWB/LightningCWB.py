# -*- coding: UTF-8 -*-
import requests
import xml.etree.ElementTree as ET
import time
from zipfile import ZipFile
from math import sin, asin, cos, radians, fabs, sqrt
from datetime import datetime

#URL example
#https://opendata.cwb.gov.tw/fileapi/v1/opendataapi/O-A0039-001?Authorization=CWB-6F3E0888-E834-4F41-9143-FE129D55B7E4&downloadType=WEB&format=KMZ
#NTU coordinate
#25°01'00.2"N 121°32'40.0"E
#25.01672N 121.54444E
NTU = (121.5444, 25.0167)
def haversine(lon1, lat1): # 经度1，纬度1，经度2，纬度2 （十进制度数）
	"""
	Calculate the great circle distance between two points
	on the earth (specified in decimal degrees)
	"""
	# 将十进制度数转化为弧度
	lon2, lat2 = NTU
	lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
	
	# haversine公式
	dlon = lon2 - lon1
	dlat = lat2 - lat1
	a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
	c = 2 * asin(sqrt(a))
	r = 6371 # 地球平均半径，单位为公里
	return c * r
#'''
dataset = set()
old_dataset = set()
while True:
	params = {
		'Authorization': 'CWB-6F3E0888-E834-4F41-9143-FE129D55B7E4',
		'downloadType': 'WEB',
		'format': 'KMZ'
		}
	ok = True
	try:
		r = requests.get('https://opendata.cwb.gov.tw/fileapi/v1/opendataapi/O-A0039-001', params = params)
		open('my_file.kmz', 'w').write(r.content)
	except:
		"Something error"
		ok = False
	if ok:
		if r.status_code == 200:
			with ZipFile('my_file.kmz', mode='r') as z:
				z.extractall()
		else:
			print "status code =", r.status_code
	#'''
	#with ZipFile('O-A0039-001.kmz', mode='r') as z:
	#	z.extractall()
	num = 0
	date = ''
	start_date = None
	tree = ET.parse('./doc.kml')
	for child in tree.iter():
		text = child.text
		if child.tag.find('name') >= 0:
			if text.startswith('中央氣象局閃電資料'.decode('utf-8')):
				tmp = text.split()
				start_date = datetime.strptime(tmp[1] + ' ' + tmp[2], '%Y-%m-%d %H:%M')
				#print "start_date =", start_date
			elif text.startswith('閃電資料'.decode('utf-8')):
				num = int(text.split()[1][1:].split('筆'.decode('utf-8'))[0])
				print "Get {} Lightning data, {}".format(num, start_date)
			else:
				tmp = text.find('-')
				date = text[tmp + 1:]
				#print "date =", date
				num -= 1
				if num < 0:
					print "Lightning number error"
			#print child.tag, ",", child.text
		elif child.tag.find('description') >= 0:
			tmp = text.split()
			if tmp[3] + ' ' + tmp[4] == date:
				km = int(haversine(float(tmp[6]), float(tmp[8])) + 0.5)
				if km < 40:
                                        if tmp[1] == '雲間'.decode('utf-8'):
                                            flash_type = 'IC'
                                        else:
                                            flash_type = 'CG'
					data = (date, km, flash_type)
					dataset.add(data)
					#print "add", data
			else:
				print "Lightning date error"
			#print child.tag, child.text
	if num != 0:
		print "Lightning number error"
	f = open('CWB_log.csv', 'r')
	for line in f:
		if not line.startswith('dataTime'):
			date = datetime.strptime(line.strip().split(',')[0], '%Y-%m-%d %H:%M')
			if (date - start_date).total_seconds() < 3600:
				old_dataset.add(line)
#print old_dataset
	f.close()
	f = open('CWB_log.csv', 'a')
	cnt = 0
        lst = list(dataset)
        sort_lst = sorted(lst, key=lambda tup: datetime.strptime(tup[0],"%Y-%m-%d %H:%M"))
	for data in sort_lst:
		output = '{}, {}, {}\n'.format(data[0], data[1], data[2])
                #if output.find('CG') < 0 and output.find('IC') < 0:
                #    print "someting wrong with output"
                #    print "output = " + output
                #    print "data =", data

		if not output in old_dataset:
			f.write(output)
			cnt += 1
	print "Add {} new data".format(cnt)
	f.close()
	dataset.clear()
	old_dataset.clear()
	time.sleep(30 * 60)
