# Fetches data from TMDb and assigns it to the meta data of video files to be used with iTunes

# For movies loop through mp4 files and search TMDb for relevent movie using the typical name and year 
# For shows pass in show name and search for that show on TMDb then use that id to find informaiton about individual episodes
# For both request the cover image at 500px wide save it and add it to the file then delete the image

import requests
from mutagen.mp4 import MP4, MP4Info, MP4Cover
import os
import re
import sys
import json
import urllib.request

def findShow(show_id, season, episode):
	global api_key
	url = "https://api.themoviedb.org/3/tv/"+ str(show_id) + "/season/"+str(season)+"/episode/"+str(episode)+"?api_key=" + api_key

	payload = {}
	headers= {}

	response = requests.request("GET", url, headers=headers, data = payload)

	return json.loads(response.text)

def downloadAndSaveImage(path):
	global season_artwork
	global api_key
	url = "http://image.tmdb.org/t/p/w500/" + path + "?api_key=" + api_key
	urllib.request.urlretrieve(url, path[1:])
	season_artwork = path[1:]

def applyData(data, tagged_file):
	global season_artwork
	tagged_file = MP4(tagged_file)
	if data['season_number']:
		tagged_file['tvsn'] = int(data['season_number'])
	if data['episode_number']:
		tagged_file['tves'] = int(data['episode_number'])
	if season_artwork != "":
		with open(season_artwork, "rb") as f:
			tagged_file["covr"] = [
				MP4Cover(f.read(), imageformat=MP4Cover.FORMAT_JPEG)
			]
	if data['year']:
		tagged_file['\xa9day'] = data['year']
	if data['name']:
		tagged_file['\xa9nam'] = data['name']
	if data['overview']:
		tagged_file['desc'] = data['overview']
	
	tagged_file.save()
		
def getSeasonArtwork(show_id, season):
	global api_key
	url = "https://api.themoviedb.org/3/tv/"+ str(show_id) + "/season/"+str(season)+"?api_key=" + api_key

	payload = {}
	headers= {}

	response = requests.request("GET", url, headers=headers, data = payload)
	j = json.loads(response.text)
	downloadAndSaveImage(j['poster_path'])
	return j
	
season_artwork = ""

def main():
	global directory
	season_episode = re.compile('S[\d]{1,2}E[\d]{1,2}')
	media_format = re.compile('\.(mov|MOV|mp4|MP4)$')
	for item in os.listdir(directory):
		if season_episode.search(item):
			if media_format.search(item):
				print(item)
				season = re.compile('S[\d]{1,2}').search(item).group(0)
				episode = re.compile('E[\d]{1,2}').search(item).group(0)
				season = int(season[1:])
				episode = int(episode[1:])
				print(season)
				print(episode)

				s = getSeasonArtwork(1400, season)

				data = findShow(1400, season, episode)
				applyData(data, directory + item)
	#print(season)
	#print(episode)
	#robbo_file = MP4('test_directory/itunes_test.mp4')
	#robbo_file.add_tags()
	#robbo_file.save()
	#print(robbo_file.tags)
	#robbo_file['tvsh'] = 'Sam Malcolm SHow'
	#robbo_file['stik'] = [1

	#robbo_file.save()
	#robbo_file.pprint()
	#show = findShow()
	#print(show)
	return

api_key = "" 
directory = ""

def getCLIFlags():
	global api_key
	global directory
	api_key = sys.argv[1]
	directory = sys.argv[2]
	# path_re = re.compile('[a-zA-Z0-9\.\/_-~ ]+')
	# tf_re = re.compile('(true|True|TRUE|false|False|FALSE)')
	# tf = ""
	# path = ""
	# if (tf_re.match(sys.argv[1])):
	# 	tf = bool(sys.argv[1])
	# 	if (path_re.match(sys.argv[2])):
	# 		path = sys.argv[2]
	# elif (tf_re.match(sys.argv[2])):
	# 	tf = bool(sys.argv[2])
	# 	if (path_re.match(sys.argv[1])):
	# 		path = sys.argv[1]
	# print(path)
	# print(tf)
	# if (path != ""):
	# 	if (tf != ""):
	# 		return [path, tf]
	

isFilm = False

if __name__ == "__main__":
	getCLIFlags()
	# isFilm = flags[1]
	# dir_content = os.listdir(flags[0])
	main()
	

	#video = MP4("test.mp4")
	# # example cover art
	# video["\xa9nam"] = "Test1"
	# video["\xa9ART"] = "Test2"
	# video["\xa9alb"] = "Test3"

	# with open("cover.jpg", "rb") as f:
	# 	video["covr"] = [
	# 		MP4Cover(f.read(), imageformat=MP4Cover.FORMAT_JPEG)
	# 	]

	# video.save()


