# imports
from flask import Flask, render_template, request, send_file
import json
from elasticsearch import Elasticsearch


# initialize application
app = Flask('podcast_explorer', static_url_path="/static", static_folder='./static')


def get_es():
	return Elasticsearch()


# home page
@app.route('/', methods=['GET'])
def home():
	return app.send_static_file('UI.html')


@app.route('/search_podcast_segment', methods=['GET'])
def search_podcast_segment():
	response = {}
	es_client = get_es()
	query = request.args.get('query')

	search_result = es_client.search(\
		index="podcast_segment", \
		size=10000, \
		body={
		  "query": {
			"multi_match": {
			  "fields":  [ "title", "subtopic_name", "speaker_name", "segment_summary"],
			  "query":     query,
			  "fuzziness": "AUTO"
			}
		  }
		})
	hits = search_result['hits']['hits']
	results = [hit['_source'] for hit in hits]
	response['response'] = results
	return response


@app.route('/search_podcast_metadata', methods=['GET'])
def search_podcast_metadata():
	response = {}
	es_client = get_es()
	query = request.args.get('query')

	search_result = es_client.search(\
		index="podcast_metadata", \
		size=10000, \
		body={
		  "query": {
			"match": {
			  "video_id": query
			}
		  }
		})
	hits = search_result['hits']['hits']
	results = [hit['_source'] for hit in hits]
	response['response'] = results
	return response


@app.route('/search_podcast_guest', methods=['GET'])
def search_podcast_guest():
	response = {}
	es_client = get_es()
	query = request.args.get('query')

	search_result = es_client.search(\
		index="podcast_guest", \
		size=10000, \
		body={
		  "query": {
			"match": {
			  "guest_name": query
			}
		  }
		})
	hits = search_result['hits']['hits']
	results = [hit['_source'] for hit in hits]
	response['response'] = results
	return response


@app.route('/search_podcast_knowledge_graph', methods=['GET'])
def search_podcast_knowledge_graph():
	response = {}

	out = {}
	es_client = get_es()

	query = request.args.get('query')
	speaker_list = query.split(",")
	speakers = ['speaker_'+speaker.strip() for speaker in speaker_list]
	speakers_string = ','.join(speakers)
	node_search_result = es_client.search(\
		index=['podcast_graph_node'], \
		size=5000, \
		body={
		  "query": {
			"match": {
			  "name": speakers_string
			}
		  }
		})
	node_hits = node_search_result['hits']['hits']
	nodes = [hit['_source'] for hit in node_hits]

	node_ids = [node['id'] for node in nodes]
	node_ids_string = ','.join(node_ids)
	edge_search_result = es_client.search(\
		index=['podcast_graph_edge'], \
		size=10000, \
		body={
		  "query": {
			"match": {
			  "source": node_ids_string
			}
		  }
		})
	edge_hits = edge_search_result['hits']['hits']
	edges = [hit['_source'] for hit in edge_hits]

	additional_nodes = [edge['target'] for edge in edges]
	chunks = [additional_nodes[i:i + 1024] for i in range(0, len(additional_nodes), 1024)]
	chunk_results = []
	for chunk in chunks:
		additional_nodes_string = ','.join(chunk)
		additional_node_search_result = es_client.search(\
			index=['podcast_graph_node'], \
			size=10000, \
			body={
			  "query": {
				"match": {
				  "id": additional_nodes_string
				}
			  }
			})
		additional_node_hits = additional_node_search_result['hits']['hits']
		additional_nodes_received = [hit['_source'] for hit in additional_node_hits]
		chunk_results.extend(additional_nodes_received)

	nodes.extend(chunk_results)
	all_nodes = [dict(t) for t in {tuple(d.items()) for d in nodes}]
	out['nodes'] = all_nodes
	out['links'] = edges
	response['response'] = out
	return response


# execution starts here
if __name__ == '__main__':
	app.run(host='0.0.0.0', port=8080, debug=True)