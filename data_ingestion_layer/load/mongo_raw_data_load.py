import deepspeech
import os
import wave
import numpy as np
import ast
from pymongo import MongoClient
import datetime


def get_db():
	client = MongoClient()
	db = client.podcast
	return db


def insert_record(db, insert_dict):
	db.segment.insert(insert_dict)


def transcribe_audio_to_text(audio, pretrained_model):
	# rate = audio.getframerate()
	frames = audio.getnframes()
	buffer = audio.readframes(frames)
	# print(rate)
	# print(pretrained_model.sampleRate())
	# print(type(buffer))
	data16 = np.frombuffer(buffer, dtype=np.int16)
	# print(type(data16))

	context = pretrained_model.createStream()
	buffer_len = len(buffer)
	offset = 0
	batch_size = 16384
	text = ''
	while offset < buffer_len:
		end_offset = offset + batch_size
		chunk = buffer[offset:end_offset]
		data16 = np.frombuffer(chunk, dtype=np.int16)
		pretrained_model.feedAudioContent(context, data16)
		text = pretrained_model.intermediateDecode(context)
		offset = end_offset
	return text


def delete_file_from_path(path):
	try:
		os.remove(path)
	except OSError as e:
		print("Error: %s : %s" % (path, e.strerror))



# Main function 
def main():
	# setup pre trained model for audio to text transcribing
	model_file_path = 'deepspeech-0.6.0-models/output_graph.pbmm'
	beam_width = 500
	model = deepspeech.Model(model_file_path, beam_width)
	lm_file_path = 'deepspeech-0.6.0-models/lm.binary'
	trie_file_path = 'deepspeech-0.6.0-models/trie'
	lm_alpha = 0.75
	lm_beta = 1.85
	model.enableDecoderWithLM(lm_file_path, trie_file_path, lm_alpha, lm_beta)

	# get MongoDb client
	podcast_db = get_db()

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

		# iterate over each audio segment for this podcast
		for segment in audio_segments:
			print("Processing file : ", segment)
			segment_name = segment.split(".")[0]
			segment_properties = segment_name.split("#")

			# read wav audio file for this segment
			wav_audio = wave.open(podcast+'/'+segment, 'r')
			
			# transcribe this audio segment to text
			raw_text = transcribe_audio_to_text(wav_audio, model)

			# read metadata for this podcast
			with open(podcast+'/'+metadata_filename, "r") as metadata:
				dict_metadata = ast.literal_eval(metadata.read())
				title = dict_metadata['title']

			# create MongoDb record corresponding to this audio segment
			record = {}
			record['video_id'] = segment_properties[0]
			record['title'] = title
			record['subtopic_name'] = segment_properties[1].split("(")[0]
			record['subtopic_order'] = segment_properties[1].split("(")[1].replace(')','')
			record['speaker_name'] = segment_properties[2].split("(")[0]
			record['speaker_order'] = segment_properties[2].split("(")[1].replace(')','')
			record['start_timestamp'] = str(datetime.timedelta(seconds=int(segment_properties[3])))
			record['end_timestamp'] = str(datetime.timedelta(seconds=int(segment_properties[4])))
			record['raw_text'] = raw_text
			
			# insert MongoDb record into the collection
			insert_record(podcast_db, record)

			# delete wav audio file for this segment
			delete_file_from_path(podcast+'/'+segment)


# execution starts here 
if __name__=="__main__": 
	main() 