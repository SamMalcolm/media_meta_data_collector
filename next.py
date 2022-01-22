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
	response = requests.request("GET", url)
	j = json.loads(response.text)
	classification = ""
	for item in j['results']:
		if item['iso_3166_1'] == "US":
			classification = item['release_dates'][0]['certification']
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


def getData():
	global contentName
	global api_key
	global isTV
	if isTV:
		url = "https://api.themoviedb.org/3/search/tv?query=" + contentName
	else:
		url = "https://api.themoviedb.org/3/search/movie?query=" + contentName
	url += "&api_key=" + api_key
	response = requests.request("GET", url)
	show_data = json.loads(response.text)
	show_data = show_data.results[0]

	# GET DATA WITH ID NOW
	if isTV == False:
		url = "https://api.themoviedb.org/3/movie/" + str(show_data.id) + "?api_key=" + api_key
	else:
		season = re.compile('(S|Series )[\d]{1,2}' ,re.I).search(filePath).group(0)
		episode = re.compile('(E|Episode )[\d]{1,2}' ,re.I).search(filePath).group(0)
		season = int(re.compile('[\d]+').search(season).group(0))
		episode = int(re.compile('[\d]+').search(episode).group(0))
		url = "https://api.themoviedb.org/3/tv/" + str(show_data.id) +'/season/' + str(season) + '/episode/' + str(episode) + "?api_key=" + api_key
	response = requests.request("GET", url)
	j = json.loads(response.text)
	if os.path.isfile(j['poster_path']):
		return {key: value for (key, value) in (show_data.items() + j.items())}
	else:
		downloadAndSaveImage(j['poster_path'])
		return {key: value for (key, value) in (show_data.items() + j.items())}

def subtitlesExistForItem(item):
	print(item)
	fileExtPattern = re.compile('\.[a-zA-Z0-9]+$')
	print(fileExtPattern.findall(item)[0])
	srtStr = item.replace(fileExtPattern.findall(item)[0], '.srt')
	if os.path.exists(srtStr):
		return srtStr
	else:
		return False


def conversion(filePath):
	global isTV, contentName, isMovie, contentID,hasSubtitlesFileAvailable, isNiceFormat

	media_format = re.compile('\.(mov|MOV|mp4|MP4|m4v)$')

	subtitlesFound = subtitlesExistForItem(filePath)
	if subtitlesFound:
		hasSubtitlesFileAvailable = True

	if media_format.search(filePath):
		isNiceFormat = True

	if isNiceFormat == False or hasSubtitlesFileAvailable:
		outputFilePath = filePath[:-4] + '.mp4'
		process = []
		process.append("ffmpeg")
		process.append("-i")
		process.append(filePath)
		if hasSubtitlesFileAvailable:
			process.append('-i')
			process.append(subtitlesFound)
			process.append('-c:s mov_text')
		subprocess.call(process)
		return outputFilePath
	else:
		return filePath

def applyData(filePath):
	global data, artwork
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
		with open(data['poster_path'], "rb") as f:
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
		cast_crew_data = getCastandCrew(data['id'], "tv")
	else:
		cast_crew_data = getCastandCrew(data['id'], "movie")
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

	rating = getClassification(data['id'])
	tagged_file['----:com.apple.iTunes:iTunEXTC'] = str.encode(
		"b'mpaa|" + rating + "|300|")
	tagged_file.save()


	

def processFilePath(filePath):
	global isTV, contentName, isMovie, contentID,hasSubtitlesFileAvailable, isNiceFormat, data, artwork
	print("Processing")

	# Determine if SRT exists and if file is the right format
	filePath = conversion(filePath)

	# Determine if TV Show, if not done already
	if isTV == False:
		tvFilePattern = re.compile('(S[\d]{1,2}E[\d]{1,2}|Series [\d]+,? Episode [\d]+)' ,re.I)
		if filePath.search(tvFilePattern):
			isTV = True

	info = PTN.parse(filePath)
	info.title = re.sub(re.compile("[\d]{4,4}"), "", info.title.replace)

	# Determine content name if not done alread
	if contentName != "":
		contentName = info.title

	# Get Text Based meta data
	data = getData()
	applyData(filePath)

	# Garbage collection
	if artwork != "":
		subprocess.call(["unlink", artwork])

	try:
		subprocess.call(["cp", filePath, '/Volumes/Sam Malcolm/itunes_media_server/Automatically add to TV/'])
		subprocess.call(["unlink", filePath])
	except:
		print("Couldnt move file")



def main(filePath):
	# If item is file, process it, if its a directory, recursively call main() on its contents.
	if (os.path.isdir(filePath) == False):
		processFilePath(filePath)
	else:
		for item in os.listdir(filePath):
			main(item)

isTV = False
contentName = ""
isMovie = False
contentID = 0
hasSubtitlesFileAvailable = False
isNiceFormat = False
data = {}

if __name__ == "__main__":
	try:
		opts, args = getopt.getopt(sys.argv[1:], "i:d:n:t", ["input=", "id=", "name=", "isTV"])
	except getopt.GetoptError:
		print ('test.py -i <inputfile> -n <content_name>')
		sys.exit(2)
	for opt, arg in opts:
		if opt in ("-i", "--input"):
			filePath = arg
		elif opt in ("-n", "--name"):
			contentName = arg
		elif opt in ("-d", "--id"):
			contentID = arg
		elif opt in ("--isTV", "-tv"):
			isTV = True
	main(filePath)