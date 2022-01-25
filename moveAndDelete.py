import sys, getopt, json, re, os, subprocess

def moveAndDeleteMethod(filePath):
	subprocess.call(["cp", filePath, '/Volumes/Sam Malcolm/itunes_media_server/Automatically Add to TV.localized/'])
	subprocess.call(["unlink", filePath])


if __name__ == "__main__":
	try:
		opts, args = getopt.getopt(sys.argv[1:], "i:", ["input="])
	except getopt.GetoptError:
		print ('test.py -i <inputfile> -n <content_name>')
		sys.exit(2)
	for opt, arg in opts:
		if opt in ("-i", "--input"):
			filePath = arg
	moveAndDeleteMethod(filePath)