import os
import wave
import ast
from pymongo import MongoClient
import gridfs
import datetime


def get_db():
	client = MongoClient()
	db = client.podcast
	return db


def get_fs(db):
	fs = gridfs.GridFS(db)
	return fs


def insert_record(db, insert_dict):
	db.segment.insert(insert_dict)


def save_to_fs(fs, file):
	with open(file, "rb") as f:
		data = f.read()
	return fs.put(data, encoding='utf-8', content_type="audio/wav")


def delete_file_from_path(path):
	try:
		os.remove(path)
	except OSError as e:
		print("Error: %s : %s" % (path, e.strerror))



# Main function 
def main():
	# get MongoDb client
	podcast_db = get_db()
	podcast_fs = get_fs(podcast_db)

	# find all podcast directories
	podcasts = [x[0] for x in os.walk(".") if "podcast_" in x[0]]
	for podcast in podcasts:
		all_files = os.listdir(podcast)

		# find metadata file for this podcast, ignore if no metadata file found
		try:
			metadata_filename = [file for file in all_files if file.endswith(".txt")][0]
		except:
			print("Exiting. No metadata found for podcast ", podcast)
			continue

		# find all wav audio files for this podcast
		audio_segments = [file for file in all_files if file.endswith(".wav")]

		# read metadata for this podcast
		with open(podcast+'/'+metadata_filename, "r") as metadata:
			dict_metadata = ast.literal_eval(metadata.read())
			title = dict_metadata['title']
			
		# iterate over each audio segment for this podcast
		for segment in audio_segments:
			print("Processing file : ", segment)
			segment_name = segment.split(".")[0]
			segment_properties = segment_name.split("#")

			# read audio properties
			wav_audio = wave.open(podcast+'/'+segment, 'r')
			wav_params = wav_audio.getparams()
			nchannels = wav_params[0]
			sampwidth = wav_params[1]
			framerate = wav_params[2]
			nframes = wav_params[3]
			comptype = wav_params[4]
			compname = wav_params[5]
			wav_audio.close()

			# save wav file to gridfs
			gridfs_key = save_to_fs(podcast_fs, podcast+'/'+segment)
			
			# create MongoDb record corresponding to this audio segment
			record = {}
			record['video_id'] = segment_properties[0]
			record['title'] = title
			record['subtopic_name'] = segment_properties[1].split('(')[0]
			record['subtopic_order'] = segment_properties[1].split('(')[1].replace(')','')
			record['speaker_name'] = segment_properties[2].split('(')[0]
			record['speaker_order'] = segment_properties[2].split('(')[1].replace(')','')
			record['start_timestamp'] = str(datetime.timedelta(seconds=int(segment_properties[3])))
			record['end_timestamp'] = str(datetime.timedelta(seconds=int(segment_properties[4])))
			record['gridfs_key'] = gridfs_key
			record['nchannels'] = nchannels
			record['sampwidth'] = sampwidth
			record['framerate'] = framerate
			record['nframes'] = nframes
			record['comptype'] = comptype
			record['compname'] = compname
			record['segment_transcript'] = None
			
			# insert MongoDb record into the collection
			insert_record(podcast_db, record)

			# delete wav audio file for this segment
			delete_file_from_path(podcast+'/'+segment)


# execution starts here 
if __name__=="__main__": 
	main() 