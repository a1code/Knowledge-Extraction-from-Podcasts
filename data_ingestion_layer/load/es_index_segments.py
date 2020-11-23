from summarizer import Summarizer
import json 
from pymongo import MongoClient
from elasticsearch import Elasticsearch
import ast
import os


def get_db():
	client = MongoClient()
	db = client.podcast
	return db


def get_es():
	return Elasticsearch()


def get_unprocessed_podcasts():
	video_ids = []
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

		# read metadata for this podcast
		with open(podcast+'/'+metadata_filename, "r") as metadata:
			dict_metadata = ast.literal_eval(metadata.read())
			video_ids.append(dict_metadata['video_id'])
	return video_ids


# function for text summarization
def summarize_segment(text, pretrained_model):
	result = pretrained_model(text, num_sentences=3)
	summary = ''.join(result)
	return summary



# Main function 
def main():
	# setup text summarization model
	model = Summarizer()

	# get MongoDb client
	podcast_db = get_db()

	# get elasticsearch client
	es_client = get_es()
	
	# get video ids for the podcasts to be indexed
	podcasts_to_be_indexed = get_unprocessed_podcasts()

	count = 0
	# read segments from raw data archive that are not indexed to elasticsearch
	for obj in podcast_db.segment.find({"video_id": {"$in" : podcasts_to_be_indexed}}):
		# get segment summary
		obj['segment_summary'] = summarize_segment(obj['raw_text'], model)
		
		obj.pop('_id', None)
		obj.pop('raw_text', None)
		
		# index segment to elasticsearch
		es_client.index(index="podcast_segment", body=json.dumps(obj))

		count = count + 1
	print(str(count), " records indexed successfully.")


# execution starts here 
if __name__=="__main__": 
	main()