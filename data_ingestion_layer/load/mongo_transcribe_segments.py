import deepspeech
import os
import wave
import numpy as np
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


def update_record(db, insert_dict):
	result = db.segment.find_one_and_update({ "_id": insert_dict['_id'] },\
	{
		"$set": { "segment_transcript": insert_dict['segment_transcript']}\
	})


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
	podcast_fs = get_fs(podcast_db)

	# find all segments that are not transcribed
	for segment in podcast_db.segment.find({"segment_transcript": None}, \
		no_cursor_timeout=True):
		key = segment['gridfs_key']
		
		# read wav audio file for this segment
		data = podcast_fs.get(key)
		audio = wave.open(data, 'rb')

		# transcribe this audio segment to text
		transcript = transcribe_audio_to_text(audio, model)
		audio.close()
		# print(transcript)
		segment['segment_transcript'] = transcript
			
		# add updated MongoDb record into the collection
		update_record(podcast_db, segment)



# execution starts here 
if __name__=="__main__": 
	main() 