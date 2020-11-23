from elasticsearch import helpers, Elasticsearch
import csv


def get_es():
	return Elasticsearch()


def index_nodes(file):
	with open(file) as f:
		reader = csv.DictReader(f)
		helpers.bulk(es, reader, index='podcast_graph_node')

def index_edges(file):
	with open(file) as f:
		reader = csv.DictReader(f)
		helpers.bulk(es, reader, index='podcast_graph_edge')


# execution starts here
if __name__ == '__main__':
	es = get_es()

	index_nodes('./knowledge_graph/nodes.csv')
	index_edges('./knowledge_graph/edges.csv')