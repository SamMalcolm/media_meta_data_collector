from mutagen.mp4 import MP4
import sys
if __name__ == "__main__": 
    print("Checking ")
    print(sys.argv[0])
    mp4File = MP4(sys.argv[1])
    print(mp4File.pprint())