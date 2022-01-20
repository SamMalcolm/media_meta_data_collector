import xml.dom.minidom
import requests
from mutagen.mp4 import MP4, MP4Info, MP4Cover

import sys, getopt, json, re, os, subprocess
import urllib.request
from datetime import datetime, time, date
import cv2
from pathlib import Path

def conversion(filePath):
	global isTV, contentName, isMovie, contentID,hasSubtitlesFileAvailable, isNiceFormat

	media_format = re.compile('\.(mov|MOV|mp4|MP4|m4v)$')

	if media_format.search(filePath):
		isNiceFormat = True

	if isNiceFormat == False or hasSubtitlesFileAvailable:
		outputFilePath = ""
		process = []
		process.append("ffmpeg")
		process.append("-i")
		process.append(filePath)

		subprocess.call(process)

		return outputFilePath
	else:
		return filePath
	

def processFilePath(filePath):
	global isTV, contentName, isMovie, contentID,hasSubtitlesFileAvailable, isNiceFormat
	print("Processing")

	# Determine if SRT exists and if file is the right format
	filePath = conversion(filePath)

	# Determine if TV Show, if not done already

	# Determine content name if not done alread

	# Get Text Based meta data

	# Get image

	# Garbage collection

	# Move to add to apple Tv directory.



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