# Fetches data from TMDb and assigns it to the meta data of video files to be used with iTunes

import requests
import mutagen
import os
import re
import sys

def findShow(name):
	print(name)

def main():
	findShow("Seinfeld")
	return

def getCLIFlags():
	return [sys.argv[1], sys.argv[2]]

isFilm = False

if __name__ == "__main__":
	directory = getCLIFlags()
	isFilm = bool(sys.argv[2])
	dir_content = os.listdir(directory[0])
	for folder in dir_content:
		print(folder)
	print(isFilm)
	robbo_file = mutagen.File('robbo.mp3')
	# robbo_file['title'] = 'Neil RObertson'
	robbo_file.pprint()

	main()