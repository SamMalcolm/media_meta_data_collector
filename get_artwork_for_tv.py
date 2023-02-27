import os
import sys
import requests
import requests_cache
from mutagen.mp4 import MP4
from mutagen.id3 import APIC
import json
from config import api_key

requests_cache.install_cache('cache')

def get_artwork(url, width=1920, height=1080, format='jpg'):
	url = url.format(w=width, h=height, f=format)
	r = requests.get(url)
	r.raise_for_status()
	return r.content

def get_show_info(show_name):
	url = f"https://uts-api.itunes.apple.com/uts/v2/search/incremental?sf=143441&locale=en-AU&caller=wta&utsk=35a0fc8b291d746%3A%3A%3A%3A%3A%3Af954d07ebc8a136&v=34&pfm=desktop&q={show_name}"
	r = requests.get(url)
	r.raise_for_status()
	data = r.json()
	if 'results' not in data:
		return None
	result = data['results'][0]
	show_id = result['data']['canvas']['id']
	return (show_id, result['data']['name'])

def get_season_artwork(show_id):
	url = f"https://uts-api.itunes.apple.com/uts/v2/show/{show_id}/itunesSeasons?sf=143441&locale=en-AU&caller=wta&utsk=def7345016abc82%3A%3A%3A%3A%3A%3Ad0e3fb52896c47a&v=34&pfm=desktop"
	r = requests.get(url)
	r.raise_for_status()
	data = r.json()
	if 'seasons' not in data:
		return None
	seasons = data['seasons']
	artwork_urls = []
	for season in seasons:
		artwork_url = season.get('artworkUrl', None)
		if artwork_url:
			artwork_urls.append(artwork_url)
	return artwork_urls

def get_episode_artwork(show_name, season_number, episode_number):
	url = f"https://api.themoviedb.org/3/search/tv?api_key={api_key}&language=en-US&query={show_name}"
	r = requests.get(url)
	r.raise_for_status()
	data = r.json()
	if 'results' not in data or len(data['results']) == 0:
		return None
	show_id = data['results'][0]['id']
	url = f"https://api.themoviedb.org/3/tv/{show_id}/season/{season_number}/episode/{episode_number}?api_key={api_key}&language=en-US"
	r = requests.get(url)
	r.raise_for_status()
	data = r.json()
	if 'still_path' not in data or not data['still_path']:
		return None
	url = f"https://image.tmdb.org/t/p/original{data['still_path']}"
	r = requests.get(url)
	r.raise_for_status()
	return r.content

def process_file(path):
	_, ext = os.path.splitext(path)
	if ext.lower() != '.mp4':
		return

	tags = MP4(path)
	show_name = tags.get('\xa9nam', None)
	season_number = tags.get('tvsn', None)
	episode_number = tags.get('tves', None)

	if not show_name or not season_number or not episode_number:
		return

	show_id, show_name = get_show_info(show_name)
	if not show_id:
		return

	season_artwork_urls = get_season_artwork(show_id)

	if not season_artwork_urls:
		return

	season_artwork_paths = []
	for url in season_artwork_urls:
		artwork = get_artwork(url)
		season_artwork_path = f"season_{season_number}_artwork.jpg"
		with open(season_artwork_path, 'wb') as f:
			f.write(artwork)
		season_artwork_paths.append(season_artwork_path)

		episode_artwork = get_episode_artwork(show_name, season_number, episode_number)

		if not episode_artwork:
			return

		episode_artwork_path = f"episode_{episode_number}_artwork.jpg"
		with open(episode_artwork_path, 'wb') as f:
			f.write(episode_artwork)

		tags['covr'] = [
			APIC(
				encoding=3,
				mime='image/jpeg',
				type=3,
				desc='Cover',
				data=episode_artwork
			)
		]

		for i, path in enumerate(season_artwork_paths):
			tags[f'covr.{i+1}'] = [
				APIC(
					encoding=3,
					mime='image/jpeg',
					type=3,
					desc=f'Season {i+1} Cover',
					data=get_artwork(path)
				)
			]

		tags.save()

		for path in season_artwork_paths + [episode_artwork_path]:
			os.remove(path)
		
def process_folder(folder):
	for name in os.listdir(folder):
		path = os.path.join(folder, name)
	if os.path.isdir(path):
		process_folder(path)
	else:
		process_file(path)

if __name__ == '__main__':
	process_folder(sys.argv[1])