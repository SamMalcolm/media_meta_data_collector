# Needs to be able to force the use of a set ID
# Needs refactoring, ie should only download the art for seasons of tv shows once not for every file

import xml.dom.minidom
import requests
from mutagen.mp4 import MP4, MP4Info, MP4Cover
import sys, getopt, json, re, os, subprocess
import urllib.request
from datetime import datetime, time, date
import cv2
from pathlib import Path
import PTN
from config import api_key
from moveAndDelete import moveAndDeleteMethod

artwork = ''

def getCastandCrew(film_id, media_kind):
	global api_key
	url = "https://api.themoviedb.org/3/"+media_kind + \
		"/" + str(film_id) + "/credits?api_key=" + api_key
	response = requests.request("GET", url)
	j = json.loads(response.text)
	return j

def getClassification(id):
	global api_key, isTV

	if isTV:
		url = "https://api.themoviedb.org/3/tv/" + \
		str(id) + "/content_ratings?api_key=" + api_key
	else: 
		url = "https://api.themoviedb.org/3/movie/" + \
		str(id) + "/release_dates?api_key=" + api_key
	print(url)
	response = requests.request("GET", url)
	j = json.loads(response.text)
	classification = ""
	if "results" in j:
		for item in j['results']:
			if item['iso_3166_1'] == "US" and "release_dates" in item:
				classification = item['release_dates'][0]['certification']
			elif "rating" in item: 
				classification = item["rating"]
			
	return classification

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

def downloadAndSaveImage(path):
	global artwork
	global api_key
	url = "http://image.tmdb.org/t/p/w500/" + path + "?api_key=" + api_key
	print("URL: "+"http://image.tmdb.org/t/p/w500/" +
		path + "?api_key=" + api_key[:4])
	urllib.request.urlretrieve(url, path[1:])
	artwork = path[1:]

show_id = ""
globalSzn = False
globalEp = False

def getData(filePath):
	global contentName
	global api_key
	global isTV
	global show_id
	global contentID
	global year
	global globalSzn
	global globalEp
	print("GETTING DATA FOR " + contentName)
	if isTV:
		url = "https://api.themoviedb.org/3/search/tv?query=" + contentName
	else:
		url = "https://api.themoviedb.org/3/search/movie?query=" + contentName
	
	if year:
		url += "&year=" + year
	url += "&api_key=" + api_key
	print("Checking URL: " + url)
	response = requests.request("GET", url)
	show_data = json.loads(response.text)
	if len(show_data["results"]) > 0:
		show_data = show_data["results"][0]
		if isTV:
			show_id = show_data["id"]

		# GET DATA WITH ID NOW
		if isTV == False:
			url = "https://api.themoviedb.org/3/movie/" + str(show_data["id"]) + "?api_key=" + api_key
		else:
			if globalSzn and globalEp:
				season = globalSzn
				episode = globalEp
			else:
				season = re.compile('(S|Series |Season )[\d]{1,2}' ,re.I).search(filePath).group(0)
				episode = re.compile('(E|Episode )[\d]{1,2}' ,re.I).search(filePath).group(0)
				season = int(re.compile('[\d]+').search(season).group(0))
				episode = int(re.compile('[\d]+').search(episode).group(0))
			url = "https://api.themoviedb.org/3/tv/" + str(show_data["id"]) +'/season/' + str(season) + '/episode/' + str(episode) + "?api_key=" + api_key
			globalSzn = False
			globalEp = False
		response = requests.request("GET", url)
		j = json.loads(response.text)
		print(j)
		if isTV:
			tvArtResponse = requests.request("GET", "https://api.themoviedb.org/3/tv/" + str(show_data["id"]) +'/season/' + str(season) + "?api_key=" + api_key)
			tvArt = json.loads(tvArtResponse.text)
			if "poster_path" in tvArt and tvArt['poster_path']:
				downloadAndSaveImage(tvArt['poster_path'])
		if "poster_path" in j and j["poster_path"]:
			
			if os.path.isfile(j['poster_path']) == False:
				downloadAndSaveImage(j['poster_path'])
		return {**show_data, **j}
	else:
		return False

def subtitlesExistForItem(item):
	print("Checking for Subs")
	fileExtPattern = re.compile('\.[a-zA-Z0-9]+$')
	srtStr = item.replace(fileExtPattern.findall(item)[0], '.srt')
	if os.path.exists(srtStr):
		print("Subs Found")
		return srtStr
	else:
		return False


def conversion(filePath):
	global isTV, contentName, isMovie, contentID,hasSubtitlesFileAvailable, isNiceFormat, forceConversion

	media_format = re.compile('\.(mov|MOV|mp4|MP4)$', re.I)

	subtitlesFound = subtitlesExistForItem(filePath)
	
	if subtitlesFound:
		hasSubtitlesFileAvailable = True
		
	if media_format.search(filePath):
		print("Looks like a nice format!")
		isNiceFormat = True

	if isNiceFormat and hasSubtitlesFileAvailable:
		outputFilePath = filePath[:-4] + '-with-subs-mmdc.mp4'	
	else: 
		outputFilePath = filePath[:-4] + '-mmdc.mp4'

	print("\n\nOUTPUT FILE\n\n")
	print(outputFilePath)

	print("Nice Format? " + str(isNiceFormat))
	print("Subs? " + str(hasSubtitlesFileAvailable))
	if isNiceFormat == False or hasSubtitlesFileAvailable or forceConversion:
		# ffmpeg -i ~/Desktop/The\ Pants\ Tent.mp4  -c:v libx265 -crf 28 -c:a aac -b:a 128k -tag:v hvc1 output.mp4
		# ffmpeg -i  -ss 00:01:00 -t 00:00:30 -c:v libx265 -tag:v hvc1 -preset medium -crf 22 -profile:v main10 -pix_fmt yuv420p10le -maxrate 40M -bufsize 80M -c:a aac -b:a 160k -ac 2 -ar 48000 -movflags +faststart ~/Desktop/output_video-2.mp4


		audio_channels = subprocess.check_output([
			"ffprobe", filePath,
			"-loglevel", "error",
			"-select_streams", "a:0",
			"-show_entries", "stream=channels",
			"-of", "default=nw=1:nk=1"
		]).strip().decode()

		if int(audio_channels) > 2:
			audio_codec = "ac3"
			audio_bitrate = "256k"
		else:
			audio_codec = "aac"
			audio_bitrate = "160k"

		process = [
			"ffmpeg", "-i", filePath]
		if hasSubtitlesFileAvailable:
			process += ["-i", subtitlesFound, "-c:s", "mov_text"]
		process += [
			"-c:v", "libx265", "-tag:v", "hvc1", "-preset", "medium",
			"-crf", "22", "-profile:v", "main10", "-pix_fmt", "yuv420p10le",
			"-maxrate", "40M", "-bufsize", "80M",
			"-c:a:0", audio_codec, "-b:a:0", audio_bitrate, "-ar", "48000",
			"-map", "0:v:0", "-map", "0:a:0",
			"-movflags", "+faststart", outputFilePath
		]

		# process = []
		# process.append("ffmpeg")
		# process.append("-i")
		# process.append(filePath)
		# if hasSubtitlesFileAvailable:
		# 	process.append('-i')
		# 	process.append(subtitlesFound)
		# 	process.append('-c:s')
		# 	process.append('mov_text')
		# process.append("-c:v")
		# process.append("libx265")
		# process.append("-tag:v")
		# process.append("hvc1")
		# process.append("-preset")
		# process.append("medium")
		# process.append("-crf")
		# process.append("22")
		# # // -profile:v main10 -pix_fmt yuv420p10le -maxrate 40M -bufsize 80M
		# process.append("-profile:v")
		# process.append("main10")
		# process.append("-pix_fmt")
		# process.append("yuv420p10le")
		# process.append("-maxrate")
		# process.append("40M")
		# process.append("-bufsize")
		# process.append("80M")
		# # -c:a aac -b:a 160k -ac 2 -ar 48000 -movflags +faststart 
		# # -af "pan=stereo|FL=FL|FR=FR|FC=FC|LFE=LFE|BL=BL|BR=BR" -c:a:0 aac -b:a:0 160k -ar 48000 -c:a:1 ac3 -b:a:1 256k -map 0:v -map 0:a -movflags +faststart output.mp4

		# ffmpeg -i input.mkv -c:v libx265 -tag:v hvc1 -preset medium -crf 22 -profile:v main10 -pix_fmt yuv420p10le -maxrate 40M -bufsize 80M  $(if [ $(ffprobe -v error -select_streams a:0 -show_entries stream=channels -of default=noprint_wrappers=1:nokey=1 input.mkv) -gt 2 ]; then echo "-c:a:1 ac3 -b:a:1 256k";  fi) -map 0:v -map 0:a -movflags +faststart output.mp4

		# process.append("-af")
		# process.append("'pan=stereo|FL=FL|FR=FR|FC=FC|LFE=LFE|BL=BL|BR=BR'")
		# process.append("-c:a:0")
		# process.append("aac")
		# process.append("-b:a:0")
		# process.append("160k")
		# process.append("-ar")
		# process.append("48000")
		# process.append("-c:a:1")
		# process.append("ac3")
		# process.append("-b:a:1")
		# process.append("256k")
		# process.append("-map")
		# process.append("0:v")
		# process.append("-map")
		# process.append("0:a")

		# process.append("-movflags")
		# process.append("+faststart")

		# process.append(outputFilePath)
		print("Calling: ")
		print(" ".join(process))
		subprocess.call(process)
		if moveAndDelete:
			subprocess.call(["unlink", filePath])
		return outputFilePath
	else:
		return filePath

def applyData(filePath):
	global data, artwork, show_id
	print("Instantiating: " + filePath)
	tagged_file= MP4(filePath)
	genres=[]
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

	if 'season_number' in data:
		tagged_file['tvsn'] = [data['season_number']]
	if 'episode_number' in data:
		tagged_file['tves'] = [data['episode_number']]
	if artwork != "":
		
		with open(artwork, "rb") as f:
			tagged_file["covr"] = [
				MP4Cover(f.read(), imageformat=MP4Cover.FORMAT_JPEG)
			]
	if 'air_date' in data:
		tagged_file['\xa9day'] = data['air_date'][:4]
	if 'name' in data:
		tagged_file['\xa9nam'] = data['name']
	if 'original_name' in data:
		tagged_file['tvsh'] = data['original_name']
		tagged_file['\xa9alb'] = data['original_name']
		tagged_file['\xa9ART'] = data['original_name']
		tagged_file['aART'] = data['original_name']
	if 'release_date' in data:
		tagged_file['\xa9day'] = data['release_date'][:4]
	vid = cv2.VideoCapture(filePath)
	width = vid.get(cv2.CAP_PROP_FRAME_WIDTH)

	if width > 1919 and width < 3839:
		tagged_file['hdvd'] = [2]
	elif width < 1919 and width > 1279:
		tagged_file['hdvd'] = [1]
	elif width > 3839:
		tagged_file['hdvd'] = [3]
	else:
		tagged_file['hdvd'] = [0]

	if isTV:
		cast_crew_data = getCastandCrew(show_id, "tv")
	else:
		cast_crew_data = getCastandCrew(data['id'], "movie")
	cast = []
	directors = []
	screenwriters = []
	producers = []
	producer_re = re.compile("Producer$")

	if "cast" in cast_crew_data:
		for cast_member in cast_crew_data['cast']:
			cast.append(cast_member['name'])

	if "crew" in cast_crew_data:
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
	print(data)
	if isTV:
		rating = getClassification(show_id)
	else: 
		rating = getClassification(data['id'])
	tagged_file['----:com.apple.iTunes:iTunEXTC'] = str.encode(
		"b'mpaa|" + rating + "|300|")

	if isTV:
		tagged_file['stik'] = [10]
	else:
		tagged_file['stik'] = [9]
	tagged_file.save()


	

def processFilePath(filePath):
	global isTV, contentName, isMovie, contentID,hasSubtitlesFileAvailable, isNiceFormat, data, artwork, moveAndDelete, forceConversion, globalSzn, globalEp

	# Determine if SRT exists and if file is the right format
	print("Checking if we need to convert: " + filePath)
	ogFilePath = filePath
	if ogFilePath.endswith(".mp4"):
		ogTags = MP4(ogFilePath)
	else:
		ogTags = False
	print("OG TAGS")
	print(ogTags)
	filePath = conversion(filePath)
	if ogTags and 'stik' in ogTags and ogTags['stik'] == [10]:
		isTV = True
		globalSzn = ogTags['tvsn'][0]
		globalEp = ogTags['tves'][0]

	# Determine if TV Show, if not done already
	if isTV == False:
		tvFilePattern = re.compile('(S[\d]{1,2}E[\d]{1,2}|Series [\d]+,? Episode [\d]+|Season [\d]+ Episode [\d]+)' ,re.I)
		if tvFilePattern.search(filePath):
			isTV = True

	fileName = re.compile("\/[\w\d\s.\[\]\-,'\(\)+]+$").search(filePath).group(0)
	print(fileName)
	info = PTN.parse(fileName)

	print(info)

	if contentName == "":

		if 'title' in info:
			info["title"] = re.sub(re.compile("\[.+\] ?"), "", info['title'])
			info["title"] = re.sub(re.compile("THEATRICAL"), "", info['title'])
			info["title"] = re.sub(re.compile("[\d]{4,4}"), "", info['title'])
			info["title"] = re.sub(re.compile("\..+$"), "", info['title'])
			# if re.compile("\/.+$").search(info['title']).groups() > 0:
			# 	info["title"] = re.compile("\/.+$").search(info['title']).group(0)[1:]

	# Determine content name if not done alread
	print(contentName)
	if contentName == "" and "title" in info:
		contentName = info["title"]
	elif contentName == "":
		print('no name known or provided')
		exit()

	# Get Text Based meta data
	data = getData(filePath)
	if data:
		applyData(filePath)
	else:
		print("Cant get data for this! :( ")
		return

	# Garbage collection
	if artwork != "":
		subprocess.call(["unlink", artwork])

	try:
		if moveAndDelete:
			print("moving and deleting")
			moveAndDeleteMethod(filePath)
	except:
		print("Couldnt move file")



def main(filePath):
	global hasSubtitlesFileAvailable,isNiceFormat, data, contentName, contentNamePermenant, isTV, isTVPermenant
	vidPattern = re.compile("\.(MPG|MP2|MPEG|MPE|MPV|OGG|MP4|M4P|MKV|M4V|AVI|WMV|MOV|QT|FLV|SWF)$", re.I)

	hasSubtitlesFileAvailable = False
	isNiceFormat = False
	data = {}
	if contentNamePermenant is False:
		contentName = ""

	if isTVPermenant is False:
		isTV = False

	# If item is file, process it, if its a directory, recursively call main() on its contents.
	print("Checking " + filePath)
	if (os.path.isdir(filePath) == False):
		if vidPattern.search(filePath):
			processFilePath(filePath)
		else:
			print("Not a video file")
	else:
		print("Directory found, looping through items")
		for item in os.listdir(filePath):
			item = filePath + "/" + item
			print(item)
			main(item)
			

isTV = False
contentName = ""
isMovie = False
contentID = 0
hasSubtitlesFileAvailable = False
isNiceFormat = False
data = {}
moveAndDelete = False
contentNamePermenant = False
isTVPermenant = False
year = False
forceConversion = False
if __name__ == "__main__":
	try:
		opts, args = getopt.getopt(sys.argv[1:], "i:d:n:thyf:", ["input=", "id=", "name=", "isTV", "hard", "year", "force"])
	except getopt.GetoptError:
		print ('test.py -i <inputfile> -n <content_name>')
		sys.exit(2)
	for opt, arg in opts:
		if opt in ("-i", "--input"):
			filePath = arg
		elif opt in ("-n", "--name"):
			contentNamePermenant = True
			contentName = arg
		elif opt in ("-d", "--id"):
			contentID = arg
		elif opt in ("--isTV", "-tv"):
			isTVPermenant = True
			isTV = True
		elif opt in ("--hard", "-h"):
			moveAndDelete = True
		elif opt in ("--year", "-y"):
			year = arg
		elif opt in ("--force", "-f"):
			forceConversion = True
	main(filePath)

# ffmpeg -i ~/Desktop/The\ Pants\ Tent.mp4  -c:v libx265 -crf 28 -c:a aac -b:a 128k -tag:v hvc1 output.mp4