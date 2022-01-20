# Fetches data from TMDb and assigns it to the meta data of video files to be used with iTunes

# For movies loop through mp4 files and search TMDb for relevent movie using the typical name and year
# For shows pass in show name and search for that show on TMDb then use that id to find informaiton about individual episodes
# For both request the cover image at 500px wide save it and add it to the file then delete the image

# HD TAG ADDED

# The atom is named "hdvd", it's an 8 bit integer where:
# 0 - SD
# 1 - 720p
# 2 - 1080p

# ffmpeg -i input.mkv -c copy -c:s mov_text output.mp4

import xml.dom.minidom
import requests
from mutagen.mp4 import MP4, MP4Info, MP4Cover
import os
import re
import sys
import json
import subprocess
import urllib.request
from datetime import datetime, time, date
import cv2
from pathlib import Path


def findShow(show_id, season, episode):
	global api_key
	url = "https://api.themoviedb.org/3/tv/" + \
		str(show_id) + "/season/"+str(season) + \
		"/episode/"+str(episode)+"?api_key=" + api_key
	response = requests.request("GET", url)
	return json.loads(response.text)


def downloadAndSaveImage(path):
	global season_artwork
	global api_key
	print("GETTING IMAGE")
	url = "http://image.tmdb.org/t/p/w500/" + path + "?api_key=" + api_key
	print("URL: "+"http://image.tmdb.org/t/p/w500/" +
		path + "?api_key=" + api_key[:4])
	urllib.request.urlretrieve(url, path[1:])
	season_artwork = path[1:]


def applyData(data, filepath, show_id, filename):
	global season_artwork, season_data, show_data
	print(data)
	tagged_file = MP4(filepath)
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
	vid = cv2.VideoCapture(filepath)
	height = vid.get(cv2.CAP_PROP_FRAME_HEIGHT)
	width = vid.get(cv2.CAP_PROP_FRAME_WIDTH)
	print(width)

	if width > 1919 and width < 3839:
		tagged_file['hdvd'] = [2]
	elif width < 1919 and width > 1279:
		tagged_file['hdvd'] = [1]
	elif width > 3839:
		tagged_file['hdvd'] = [3]
	else:
		tagged_file['hdvd'] = [0]

	cast_crew_data = getCastandCrew(show_id, "tv")
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

	rating = getTVContentRating(show_id)
	tagged_file['----:com.apple.iTunes:iTunEXTC'] = str.encode(
		"b'mpaa|" + rating + "|300|")

	genres = []

	if 'genres' in show_data:
		for genre in show_data['genres']:
			genres.append(genre['name'])
		tagged_file['\xa9gen'] = genres

	tagged_file.save()

	# Path(filepath).rename(
		# '/Volumes/Sam Malcolm/itunes_media_server/Automatically Add to TV.localized/' + filename)
	# subprocess.call(['mv', filepath, '/Volumes/Sam\ Malcolm/itunes_media_server/Automatically\ Add\ to\ TV.localized'])


season_data = {}
show_data = {}


def getShowData(show_id):
	global api_key, show_data
	url = "https://api.themoviedb.org/3/tv/" + \
		str(show_id) + "?api_key=" + api_key
	response = requests.request("GET", url)
	show_data = json.loads(response.text)
	return show_data


def getTVContentRating(show_id):
	global api_key
	url = "https://api.themoviedb.org/3/tv/" + \
		str(show_id) + "/content_ratings?api_key=" + api_key
	response = requests.request("GET", url)
	j = json.loads(response.text)
	rating = ""
	for item in j['results']:
		if item['iso_3166_1'] == "US":
			rating = item['rating']
	return rating


def getSeasonArtwork(show_id, season):
	print("GETTING IMAGE")
	global api_key, directory, season_data
	url = "https://api.themoviedb.org/3/tv/" + \
		str(show_id) + "/season/"+str(season)+"?api_key=" + api_key
	response = requests.request("GET", url)
	j = json.loads(response.text)
	season_data = j
	print(directory)
	print(j)
	if j['poster_path']:
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
	url = "https://api.themoviedb.org/3/movie/" + \
		str(id) + "?api_key=" + api_key
	response = requests.request("GET", url)
	j = json.loads(response.text)
	if os.path.isfile(j['poster_path']):
		return j
	else:
		downloadAndSaveImage(j['poster_path'])
		return j


def getCastandCrew(film_id, media_kind):
	global api_key
	url = "https://api.themoviedb.org/3/"+media_kind + \
		"/" + str(film_id) + "/credits?api_key=" + api_key
	response = requests.request("GET", url)
	j = json.loads(response.text)
	return j


def getClassification(film_id):
	global api_key
	url = "https://api.themoviedb.org/3/movie/" + \
		str(film_id) + "/release_dates?api_key=" + api_key
	response = requests.request("GET", url)
	j = json.loads(response.text)
	classification = ""
	for item in j['results']:
		if item['iso_3166_1'] == "US":
			classification = item['release_dates'][0]['certification']
	return classification


def processFilm(film_id, filepath):
	global subtitlesActioned
	subtitlesFound = subtitlesExistForItem(filepath)
	fileExtPattern = re.compile('\.[a-zA-Z0-9]+$')
	oldfilePath = filepath
	ext = fileExtPattern.findall(filepath)[0]
	newfilepath = filepath.replace(ext, '-with-subs' + ext)
	print("\n\n========\n\n")
	print(filepath)
	print(newfilepath)
	print(oldfilePath)
	if subtitlesFound and subtitlesActioned == False:
		subtitlesActioned = True
		print("\n\n\nCALLING " + " ".join(['ffmpeg', '-i', oldfilePath, '-i', subtitlesFound, '-c:s mov_text', newfilepath ]))
		print("\n\n\n\n")
		subprocess.call(['ffmpeg', '-i', oldfilePath, '-i', subtitlesFound, '-c:s mov_text', newfilepath ])
	filetags = checkTags(filepath)
	if subtitlesActioned:
		# tagged_file = MP4(newfilepath)
		print("true")
	else:
		tagged_file = MP4(oldfilePath)
	print(tagged_file.tags)
	data = getFilmData(film_id)
	tagged_file['stik'] = [9]
	genres = []

	if 'genres' in data:
		for genre in data['genres']:
			genres.append(genre['name'])
		tagged_file['\xa9gen'] = genres
	if 'overview' in data:
		tagged_file['ldes'] = data['overview']
		tagged_file['desc'] = data['overview']
	if 'title' in data:
		tagged_file['\xa9alb'] = data['title']
		tagged_file['aART'] = data['title']
		tagged_file['\xa9nam'] = data['title']
	elif 'original_title' in data:
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

	# GET CAST AND CREW

	cast_crew_data = getCastandCrew(film_id, "movie")
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
	# hdvd
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
	elif width < 1919 and width > 1279:
		tagged_file['hdvd'] = [1]
	elif width > 3839:
		tagged_file['hdvd'] = [3]
	else:
		tagged_file['hdvd'] = [0]

	# GENERATE XML AND AS AS BITES TO ----:com.apple.iTunes:iTunMOVI TAG
	rating = getClassification(film_id)
	tagged_file['----:com.apple.iTunes:iTunEXTC'] = str.encode(
		"b'mpaa|" + rating + "|300|")

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


season_data_retrieved = False
show_data_retrieved = False


def processTVShow(item, directory):
	global season_data, season_data_retrieved, show_data_retrieved
	season_episode = re.compile('(S[\d]{1,2}E[\d]{1,2}|Series [\d]+,? Episode [\d]+)' ,re.I)
	if season_episode.search(item):
		print(item)
		season = re.compile('(S|Series )[\d]{1,2}' ,re.I).search(item).group(0)
		episode = re.compile('(E|Episode )[\d]{1,2}' ,re.I).search(item).group(0)
		season = int(re.compile('[\d]+').search(season).group(0))
		episode = int(re.compile('[\d]+').search(episode).group(0))
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
		applyData(data, directory + item, item_id, item)
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
			applyData(data, directory + item, item_id, item)


def subtitlesExistForItem(item):
	print(item)
	fileExtPattern = re.compile('\.[a-zA-Z0-9]+$')
	print(fileExtPattern.findall(item)[0])
	srtStr = item.replace(fileExtPattern.findall(item)[0], '.srt')
	if os.path.exists(srtStr):
		print("SUBTITLE TRACK EXISTS")
		return srtStr
	else:
		return False


def main():
	global directory, season_data, item_id, subtitlesActioned
	media_format = re.compile('\.(mov|MOV|mp4|MP4|m4v)$')
	if os.path.isdir(directory):
		for item in os.listdir(directory):
			if media_format.search(item):
				processTVShow(item, directory + '/')
			else:
				print("Invalid media format")
				convertable_format = re.compile("\.(avi|AVI|mkv|MKV)$")
				if convertable_format.search(item):
					subprocess.call(
						['ffmpeg', '-i', directory + '/' + item, directory + '/' + item[:-4] + '.mp4'])
					if os.path.isfile(directory + '/' + item[:-4] + '.mp4'):
						subprocess.call(['rm', directory + '/' + item])
						# print("COULD HAVE CALLED: " + 'rm' + ' ' + directory + '/' + item)
						processTVShow(item[:-4] + '.mp4', directory + '/')
				else:
					print("Nothing we can do chief")
	else:
		if media_format.search(directory):
			processFilm(item_id, directory)
		else:
			print("Invalid media format")
			convertable_format = re.compile("\.(avi|AVI|mkv|MKV)$")
			if convertable_format.search(directory):

				subtitlesFound = subtitlesExistForItem(directory)
				process = ['ffmpeg', '-i', directory]
				if subtitlesFound:
					subtitlesActioned = True
					process.append('-i')
					process.append(subtitlesFound)
					process.append('-c:s mov_text')
					directory = directory + '-processed'
				process.append(directory + '.mp4')
				subprocess.call(process)
				if os.path.isfile(directory + '.mp4'):
					subprocess.call(['rm', directory])
					# print("COULD HAVE CALLED: " + 'rm' + ' ' + directory + '/' + item)
					processFilm(item_id, directory)
			else:
				print("Nothing we can do chief")
	return


api_key = ""
directory = ""
item_id = 0
subtitlesActioned = False


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

