import os
import subprocess
from pytube import Playlist
import re
import time
from datetime import datetime, timezone
from pymongo import MongoClient


def get_db():
	client = MongoClient()
	db = client.podcast
	return db


def get_processed_podcasts():
	return [obj['video_id'] for obj in get_db().segment.find()]


def delete_file_from_path(path):
	try:
		os.remove(path)
	except OSError as e:
		print("Error: %s : %s" % (path, e.strerror))



# Main function 
def main():
	# list of podcast video ids already present in the raw data archive 
	processed_podcasts = get_processed_podcasts()

	# playlist to download the podcasts from
	playlist_link = "https://www.youtube.com/watch?v=c9AbECvRt20&list=PLrAXtmErZgOdP_8GztsuKi9nrraNbKKp4"
	playlist = Playlist(playlist_link)
	
	# this fixes the empty playlist.videos list
	playlist._video_regex = re.compile(r"\"url\":\"(/watch\?v=[\w-]*)")
	print('Total number of podcasts in the playlist: ', str(len(playlist.video_urls)))

	limit = 0 # counter used to limit number of files to be downloaded
	for video in playlist.videos:
		# download no more than these many podcasts
		if(limit == 80):
			break
			
		# ignore podcasts that are already loaded to the raw data archive
		if(video.video_id in processed_podcasts):
			limit = limit + 1
			continue

		# ignore podcasts without segment information by timestamps
		if(video.description == ""):
			limit = limit + 1
			continue

		# extract metadata for this podcast
		metadata = {}
		metadata['video_id'] = video.video_id
		metadata['title'] = re.sub('[^a-zA-Z0-9 \n\.]', '_', video.title)
		metadata['description'] = video.description
		metadata['rating'] = video.rating
		metadata['length'] = video.length
		metadata['views'] = video.views
		metadata['author'] = video.author
		aware_local_now = datetime.now(timezone.utc).astimezone()
		metadata['downloaded_at'] = str(aware_local_now)

		# create directory for this podcast
		download_dir = 'podcast_'+metadata['video_id']
		os.makedirs(download_dir, exist_ok=True)

		# open a new text file to write metadata for this podcast
		with open(os.path.join(download_dir, metadata['title']+'.txt'),'w+') as f:
			# append metadata to text file
			f.write(str(metadata) + '\n')

		# start audio mp4 download stream for this podcast
		ys = video.streams.filter(only_audio=True, file_extension='mp4')
		print('Downloading : ', metadata['title'])
		ys[0].download(filename=metadata['title'])

		# to ensure mp4 is fully downloaded before further processing
		time.sleep(2)

		'''
		convert downloaded mp4 to wav file 
		RIFF (little-endian) data, WAVE audio, Microsoft PCM, 16 bit, mono 16000 Hz
		and save in the directory created for this podcast
		'''
		subprocess.call(['ffmpeg', \
			'-i', metadata['title']+'.mp4', '-acodec', 'pcm_s16le', '-ac', '1', '-ar', '16000', \
			os.path.join(download_dir, metadata['title']+'.wav')])

		# delete raw mp4 file
		delete_file_from_path(metadata['title']+'.mp4')

		limit = limit + 1


# execution starts here 
if __name__=="__main__": 
	main() 