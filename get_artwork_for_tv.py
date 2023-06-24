import os
import sys
import re
import requests
import requests_cache
from mutagen.mp4 import MP4, MP4Cover, MP4FreeForm
import json
from config import api_key
import xml.etree.ElementTree as ET
import plistlib

requests_cache.install_cache('cache')

def get_artwork(url, width=1920, height=1080, format='jpg'):
	url = url.format(w=width, h=height, f=format)
	print(url)
	r = requests.get(url)
	r.raise_for_status()
	return r.content

def get_show_info(show_name):
	st = show_name[0].replace(" ", "%20")
	url = f"https://uts-api.itunes.apple.com/uts/v2/search/incremental?sf=143441&locale=en-AU&caller=wta&utsk=35a0fc8b291d746%3A%3A%3A%3A%3A%3Af954d07ebc8a136&v=34&pfm=desktop&q={st}"
	print(url)
	r = requests.get(url)
	r.raise_for_status()
	data = r.json()
	# print(data)
	if 'data' not in data:
		return None
	result = data
	# print(result['data']['canvas']['shelves'])
	if (re.compile(show_name, re.I).search(result['data']['canvas']['shelves'][0]['items'][0]['title'])):
		show_id = result['data']['canvas']['shelves'][0]['items'][0]['id']
		show_name = result['data']['canvas']['shelves'][0]['items'][0]['title']
	else:
		return (False, False)

	
	print("SHOW ID")
	print(show_id)
	print("SHOW NAME")
	print(show_name)
	return (show_id, show_name)

def get_season_artwork(show_id, season_number):
	season_number = season_number[0]
	url = f"https://uts-api.itunes.apple.com/uts/v2/show/{show_id}/itunesSeasons?sf=143441&locale=en-AU&caller=wta&utsk=def7345016abc82%3A%3A%3A%3A%3A%3Ad0e3fb52896c47a&v=34&pfm=desktop"
	r = requests.get(url)
	r.raise_for_status()
	data = r.json()
	# print(data)
	if 'data' not in data:
		return None

	print(data['data']['seasons'])
	print(url)
	if str(season_number) in data['data']['seasons']:
		season = data['data']['seasons'][str(season_number)][0]
	elif len(data['data']['seasons'][str(season_number - 1)]) > 1:
		season = data['data']['seasons'][str(season_number - 1)][1]
	else:
		return False
	artwork_url = season['images']['coverArt16X9']['url']
	return artwork_url

def get_episode_artwork(show_name, season_number, episode_number):
	url = f"https://api.themoviedb.org/3/search/tv?api_key={api_key}&query={show_name}"
	r = requests.get(url)
	r.raise_for_status()
	data = r.json()
	if 'results' not in data or len(data['results']) == 0:
		return None
	show_id = data['results'][0]['id']
	url = f"https://api.themoviedb.org/3/tv/{show_id}/season/{season_number[0]}/episode/{episode_number[0]}?api_key={api_key}"
	r = requests.get(url)
	try:
		r.raise_for_status()
	except:
		return False
	data = r.json()
	if 'still_path' not in data or not data['still_path']:
		return None
	url = f"https://image.tmdb.org/t/p/original{data['still_path']}"
	r = requests.get(url)
	r.raise_for_status()
	return r.content

def process_file(path):
	season_artwork_paths = []
	_, ext = os.path.splitext(path)
	if ext.lower() != '.mp4':
		return

	tags = MP4(path)
	show_name = tags.get('tvsh', None)
	season_number = tags.get('tvsn', None)
	episode_number = tags.get('tves', None)
	print("SHOW: ")
	print(show_name)
	print("SEASON: ")
	print(season_number)
	print("EPSIODE: ")
	print(episode_number)
	if not show_name or not season_number or not episode_number:
		return

	show_id, show_name = get_show_info(show_name)
	if not show_id or show_id is False:
		return

	season_artwork_url = get_season_artwork(show_id, season_number)
	covers = []
	if season_artwork_url:
		artwork = get_artwork(season_artwork_url)

		
		season_artwork_path = f"season_{season_number[0]}_artwork.jpg"
		with open(season_artwork_path, 'wb') as f:
			f.write(artwork)
		season_artwork_paths.append(season_artwork_path)
		covers.append(MP4Cover(artwork, imageformat=MP4Cover.FORMAT_JPEG))
		
	episode_artwork = get_episode_artwork(show_name, season_number, episode_number)

	if episode_artwork:

		episode_artwork_path = f"episode_{episode_number[0]}_artwork.jpg"
		with open(episode_artwork_path, 'wb') as f:
			f.write(episode_artwork)
		covers.append(MP4Cover(episode_artwork, imageformat=MP4Cover.FORMAT_JPEG))
	else:
		episode_artwork_path = False

	

	# Set the covers as the value of the covr atom
	tags["covr"] = covers

	# Set the season and episode metadata keys
	tags["----:com.apple.iTunes:season"]= str.encode(str(season_number[0]))
	tags["----:com.apple.iTunes:episode"]=str.encode(str(episode_number[0]))
	tags.save()
	print(season_artwork_paths)
	for path in season_artwork_paths:
		os.remove(path)
		if  episode_artwork_path:
			os.remove(episode_artwork_path)
		
def process_folder(folder):
	print("Processing")
	print(folder)
	for name in os.listdir(folder):
		path = os.path.join(folder, name)
		if os.path.isdir(path):
			process_folder(path)
		else:
			process_file(path)

if __name__ == '__main__':
	process_folder(sys.argv[1])