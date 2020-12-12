import json 
import os
import shutil
import ast
from elasticsearch import Elasticsearch


def get_es():
	return Elasticsearch()


def delete_directory(path):
	try:
		shutil.rmtree(path)
	except OSError as e:
		print("Error: %s : %s" % (path, e.strerror))



# Main function 
def main():
	# get elasticsearch client
	es_client = get_es()

	# find all podcast directories
	podcasts = [x[0] for x in os.walk(".") if "podcast_" in x[0]]
	for podcast in podcasts:
		for file in os.listdir(podcast):
			# find metadata file for this podcast
			if file.endswith(".txt"):
				print('Processing file : ', file)

				# read metadata for this podcast
				with open(podcast+'/'+file, "r") as metadata:
					dict_metadata = ast.literal_eval(metadata.read())

					# parse guest details
					guest = {}
					guest['guest_name'] = dict_metadata['title'].split("_")[0]
					guest['guest_description'] = dict_metadata['description'].split(".")[0]
					
					# index guest details to elasticsearch
					es_client.index(index="podcast_guest", body=json.dumps(guest))


					# parse podcast metadata
					podcast_meta = {}
					podcast_meta['video_id'] = dict_metadata['video_id']
					podcast_meta['title'] = dict_metadata['title']

					desc_start_idx = dict_metadata['description'].find("OUTLINE:")
					desc_end_idx = dict_metadata['description'].find("CONNECT:")
					segments = dict_metadata['description'][desc_start_idx+8:desc_end_idx-1].strip().split('\n')[1:]
					podcast_meta['description'] = segments
					
					podcast_meta['rating'] = dict_metadata['rating']
					podcast_meta['length'] = dict_metadata['length']
					podcast_meta['views'] = dict_metadata['views']
					podcast_meta['author'] = dict_metadata['author']
					podcast_meta['downloaded_at'] = dict_metadata['downloaded_at']
					
					# index podcast metadata to elasticsearch
					es_client.index(index="podcast_metadata", body=json.dumps(podcast_meta))

					# delete directory for this podcast
					delete_directory(podcast)


# execution starts here 
if __name__=="__main__": 
	main()