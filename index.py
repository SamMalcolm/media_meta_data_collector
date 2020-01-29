# Fetches data from TMDb and assigns it to the meta data of video files to be used with iTunes

import requests
from mutagen.mp4 import MP4, MP4Info, MP4Cover
import os
import re
import sys
def findShow():
	url = "https://api.themoviedb.org/3/tv/1400/season/2/episode/12?api_key=11b3c70aaee7f6f3fffb5cd45714f229"

	payload = {}
	headers= {}

	response = requests.request("GET", url, headers=headers, data = payload)

	return response.text.encode('utf-8')

def main():
	findShow()
	return

def getCLIFlags():
	path_re = re.compile('[a-zA-Z0-9\.\/_-~ ]+')
	tf_re = re.compile('(true|True|TRUE|false|False|FALSE)')
	tf = ""
	path = ""
	if (tf_re.match(sys.argv[1])):
		tf = bool(sys.argv[1])
		if (path_re.match(sys.argv[2])):
			path = sys.argv[2]
	elif (tf_re.match(sys.argv[2])):
		tf = bool(sys.argv[2])
		if (path_re.match(sys.argv[1])):
			path = sys.argv[1]
	print(path)
	print(tf)
	if (path != ""):
		if (tf != ""):
			return [path, tf]
	

isFilm = False

if __name__ == "__main__":
	flags = getCLIFlags()
	isFilm = flags[1]
	dir_content = os.listdir(flags[0])
	for folder in dir_content:
		print(folder)
	print(isFilm)
	robbo_file = MP4('test_directory/itunes_test.mp4')
	#robbo_file.add_tags()
	#robbo_file.save()
	print(robbo_file.tags)
	#robbo_file['tvsh'] = 'Sam Malcolm SHow'
	#robbo_file['stik'] = [1

	robbo_file.save()
	robbo_file.pprint()

	video = MP4("test.mp4")
	# # example cover art
	# video["\xa9nam"] = "Test1"
	# video["\xa9ART"] = "Test2"
	# video["\xa9alb"] = "Test3"

	# with open("cover.jpg", "rb") as f:
	# 	video["covr"] = [
	# 		MP4Cover(f.read(), imageformat=MP4Cover.FORMAT_JPEG)
	# 	]

	# video.save()

	main()

	# For movies loop through mp4 files and search TMDb for relevent movie using the typical name and year 
	# For shows pass in show name and search for that show on TMDb then use that id to find informaiton about individual episodes
	# For both request the cover image at 500px wide save it and add it to the file then delete the image