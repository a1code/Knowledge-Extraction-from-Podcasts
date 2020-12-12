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



# Main function 
def main():
	# get MongoDb client
	podcast_db = get_db()

	# get elasticsearch client
	es_client = get_es()

	count = 0
	# read segments from raw data archive that have been transcribed to text
	for obj in podcast_db.segment.find({"segment_transcript": {"$ne":None}}):
		obj.pop('_id', None)
		obj.pop('gridfs_key', None)
		obj.pop('nchannels', None)
		obj.pop('sampwidth', None)
		obj.pop('framerate', None)
		obj.pop('nframe', None)
		obj.pop('comptype', None)
		obj.pop('compname', None)
		
		# index segment to elasticsearch
		es_client.index(index="podcast_segment", body=json.dumps(obj))

		count = count + 1
	print(str(count), " records indexed successfully.")


# execution starts here 
if __name__=="__main__": 
	main()