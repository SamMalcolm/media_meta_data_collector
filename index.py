# Fetches data from TMDb and assigns it to the meta data of video files to be used with iTunes

# For movies loop through mp4 files and search TMDb for relevent movie using the typical name and year 
# For shows pass in show name and search for that show on TMDb then use that id to find informaiton about individual episodes
# For both request the cover image at 500px wide save it and add it to the file then delete the image

# HD TAG ADDED

# The atom is named "hdvd", it's an 8 bit integer where:
# 0 - SD
# 1 - 720p
# 2 - 1080p

import xml.dom.minidom
import requests
from mutagen.mp4 import MP4, MP4Info, MP4Cover
import os
import re
import sys
import json
import urllib.request
from datetime import datetime, time, date
import cv2

def findShow(show_id, season, episode):
	global api_key
	url = "https://api.themoviedb.org/3/tv/"+ str(show_id) + "/season/"+str(season)+"/episode/"+str(episode)+"?api_key=" + api_key
	response = requests.request("GET", url)
	return json.loads(response.text)

def downloadAndSaveImage(path):
	global season_artwork
	global api_key
	print("GETTING IMAGE")
	url = "http://image.tmdb.org/t/p/w500/" + path + "?api_key=" + api_key
	print("URL: "+"http://image.tmdb.org/t/p/w500/" + path + "?api_key=" + api_key[:4])
	urllib.request.urlretrieve(url, path[1:])
	season_artwork = path[1:]

def applyData(data, tagged_file):
	global season_artwork, season_data, show_data
	print(data)
	tagged_file = MP4(tagged_file)
	tagged_file['stik'] = [10]
	if 'season_number' in data:
		tagged_file['tvsn'] = [data['season_number']]
	if 'episode_number' in data:
		tagged_file['tves'] = [data['episode_number']]
	if season_artwork != "":
		with open(season_artwork, "rb") as f:
			tagged_file["covr"] = [
				MP4Cover(f.read(), imageformat=MP4Cover.FORMAT_JPEG)
			]
	if 'air_date' in data:
		tagged_file['\xa9day'] = data['air_date'][:4]
	if 'name' in data:
		tagged_file['\xa9nam'] = data['name']
	if 'overview' in data:
		tagged_file['desc'] = data['overview']
	if 'original_name' in show_data:
		tagged_file['tvsh'] = show_data['original_name']
		tagged_file['\xa9alb'] = show_data['original_name']
		tagged_file['\xa9ART'] = show_data['original_name']
		tagged_file['aART'] = show_data['original_name']
	tagged_file.save()
		
season_data = {}
show_data = {}

def getShowData(show_id):
	global api_key, show_data
	url = "https://api.themoviedb.org/3/tv/"+ str(show_id) +"?api_key=" + api_key
	response = requests.request("GET", url)
	show_data = json.loads(response.text)
	return show_data

def getSeasonArtwork(show_id, season):
	print("GETTING IMAGE")
	global api_key, directory, season_data
	url = "https://api.themoviedb.org/3/tv/"+ str(show_id) + "/season/"+str(season)+"?api_key=" + api_key
	response = requests.request("GET", url)
	j = json.loads(response.text)
	season_data = j
	if os.path.isfile(directory + j['poster_path']):
		print("FOUND FILE NOT SAVING")
		return j
	else:
		print("FILE NOT FOUND RETRIEVING IMAGE")
		downloadAndSaveImage(j['poster_path'])
		return j
	
season_artwork = ""

def checkTags(filepath):
	filetags = MP4(filepath)
	filetags = filetags.tags
	return filetags

def getFilmData(id):
	global api_key
	url = "https://api.themoviedb.org/3/movie/"+ str(id) +"?api_key=" + api_key
	response = requests.request("GET", url)
	j = json.loads(response.text)
	if os.path.isfile(j['poster_path']):
		return j
	else: 
		downloadAndSaveImage(j['poster_path'])
		return j 

def getCastandCrew(film_id):
	global api_key
	url = "https://api.themoviedb.org/3/movie/"+ str(film_id) +"/credits?api_key=" + api_key
	response = requests.request("GET", url)
	j = json.loads(response.text)
	return j

def getClassification(film_id):
	global api_key
	url = "https://api.themoviedb.org/3/movie/"+ str(film_id) +"/release_dates?api_key=" + api_key
	response = requests.request("GET", url)
	j = json.loads(response.text)
	classification = ""
	for item in j['results']:
		if item['iso_3166_1'] == "US":
			classification = item['release_dates'][0]['certification']
	return classification

def processFilm(film_id, filepath):

	filetags = checkTags(filepath)
	tagged_file = MP4(filepath)
	print(tagged_file.tags)
	data = getFilmData(film_id)
	tagged_file['stik']  = [9]
	genres = []
	
	if 'genres' in data:
		for genre in data['genres']:
			genres.append(genre['name'])
		tagged_file['\xa9gen'] = genres
	if 'overview' in data:
		tagged_file['ldes'] = data['overview']
		tagged_file['desc'] = data['overview']
	if 'original_title' in data:
		tagged_file['\xa9alb'] = data['original_title']
		tagged_file['aART'] = data['original_title']
		tagged_file['\xa9nam'] = data['original_title']
	if 'poster_path' in data:
		with open(data['poster_path'][1:], "rb") as f:
			tagged_file["covr"] = [
				MP4Cover(f.read(), imageformat=MP4Cover.FORMAT_JPEG)
			]
	if 'release_date' in data:
		tagged_file['\xa9day'] = data['release_date'][:4]

	#GET CAST AND CREW

	cast_crew_data = getCastandCrew(film_id)
	cast = []
	directors = []
	screenwriters = []
	producers = []
	producer_re = re.compile("Producer$")
	for cast_member in cast_crew_data['cast']:
		cast.append(cast_member['name'])

	for crew_members in cast_crew_data['crew']:
		if crew_members['job'] == "Director":
			directors.append(crew_members['name'])
		if crew_members['department'] == "Writing":
			screenwriters.append(crew_members['name'])
		if producer_re.search(crew_members['job']):
			producers.append(crew_members['name'])
	
	xml_str = "<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">\n"
	xml_str += "<plist version=\"1.0\">\n"
	xml_str += "<dict>"
	xml_str += generateXML(cast, "cast")
	xml_str += generateXML(directors, "directors")
	xml_str += generateXML(screenwriters, "screenwriters")
	xml_str += generateXML(producers, "producers")
	xml_str += "</dict>"
	xml_str += "</plist>"

	tagged_file['----:com.apple.iTunes:iTunMOVI'] = str.encode(xml_str)
	#hdvd
	# 0 - nothing
	# 1 - 720p
	# 2 - 1080p
	# 3 - 4K
	
	vid = cv2.VideoCapture(filepath)
	height = vid.get(cv2.CAP_PROP_FRAME_HEIGHT)
	width = vid.get(cv2.CAP_PROP_FRAME_WIDTH)
	print(width)

	if width > 1919 and width < 3839:
		tagged_file['hdvd'] = [2]
	elif width <1919 and width > 719:
		tagged_file['hdvd'] = [1]
	elif width > 3839:
		tagged_file['hdvd'] = [3]
	else:
		tagged_file['hdvd'] = [0]
	
	#GENERATE XML AND AS AS BITES TO ----:com.apple.iTunes:iTunMOVI TAG
	rating = getClassification(film_id)
	tagged_file['----:com.apple.iTunes:iTunEXTC'] = str.encode("b'mpaa|" + rating + "|300|")

	tagged_file.save()
	
def generateXML(crew_arr, crew_key):
	string = ""
	string += "<key>" + crew_key + "</key>\n"
	string += "<array>\n"
	crewcount = 0
	crewmembers = []
	for member in crew_arr:
		crewcount += 1
		if crewcount < 11 and member not in crewmembers:
			crewmembers.append(member)
			string += "<dict>\n"
			string += "<key>name</key>\n"
			string += "<string>" + member + "</string>\n"
			string += "</dict>\n"
	string += "</array>"
	return string

def main():
	global directory, season_data, item_id
	season_episode = re.compile('S[\d]{1,2}E[\d]{1,2}')
	media_format = re.compile('\.(mov|MOV|mp4|MP4|m4v)$')
	season_data_retrieved = False
	show_data_retrieved = False
	if os.path.isdir(directory):
		for item in os.listdir(directory):
			if media_format.search(item):
				if season_episode.search(item):
					print(item)
					season = re.compile('S[\d]{1,2}').search(item).group(0)
					episode = re.compile('E[\d]{1,2}').search(item).group(0)
					season = int(season[1:])
					episode = int(episode[1:])
					print(season)
					print(episode)
					if 'season_number' in season_data:
						if (season_data['season_number'] != season):
							season_data_retrieved = False
					if (season_data_retrieved != True):
						s = getSeasonArtwork(item_id, season)
						season_data_retrieved = True
					if (show_data_retrieved != True):
						sh = getShowData(item_id)
						show_data_retrieved = True
					data = findShow(item_id, season, episode)
					applyData(data, directory + item)
				else:
					tags = checkTags(directory + item)
					if 'tvsh' in tags:
						
						episode = tags['tves'][0]
						season = tags['tvsn'][0]
						print("EPISODE " + str(episode))
						print("SEASON " + str(season))
						if 'season_number' in season_data:
							if (season_data['season_number'] != season):
								season_data_retrieved = False
						if (season_data_retrieved != True):
							s = getSeasonArtwork(item_id, season)
							season_data_retrieved = True
						if (show_data_retrieved != True):
							sh = getShowData(item_id)
							show_data_retrieved = True
						data = findShow(item_id, season, episode)
						applyData(data, directory + item)
	else:
		processFilm(item_id, directory)
	return

api_key = "" 
directory = ""
item_id = 0

def getCLIFlags():
	global api_key
	global directory
	global item_id
	api_key = sys.argv[1]
	directory = sys.argv[2]
	item_id = int(sys.argv[3])

if __name__ == "__main__":
	getCLIFlags()
	main()


