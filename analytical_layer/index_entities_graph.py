from elasticsearch import helpers, Elasticsearch
import csv
import os


def get_es():
	return Elasticsearch()


def index_file(file, index):
	with open(file) as f:
		reader = csv.DictReader(f)
		helpers.bulk(es, reader, index=index)


def delete_directory(path):
	try:
		shutil.rmtree(path)
	except OSError as e:
		print("Error: %s : %s" % (path, e.strerror))



# execution starts here
if __name__ == '__main__':
	es = get_es()

	# find all podcast directories
	podcasts = [x[0] for x in os.walk("./knowledge_graph") if x[0] != './knowledge_graph/all'][1:]
	for podcast in podcasts:
		# index nodes and edges for this guest
		podcast_name1 = (podcast.split("/")[2]).split("_")[:-2]
		podcast_name2 = [x.strip().lower().replace(" ", "") for x in podcast_name1]
		podcast_name3 = ''.join(podcast_name2)
		index_file(podcast+'/nodes.csv', podcast_name3+'_node_podcast')
		index_file(podcast+'/edges.csv', podcast_name3+'_edge_podcast')

		# delete CSV files for this guest
		delete_directory(guest)