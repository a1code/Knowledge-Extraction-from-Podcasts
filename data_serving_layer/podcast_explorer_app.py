# imports
from flask import Flask, request
import json
from pymongo import MongoClient
import gridfs
from elasticsearch import Elasticsearch
import wave
import os
import time
from flask_cors import CORS,cross_origin
import pygame
from pygame import mixer


# initialize application
app = Flask('podcast_explorer', static_url_path="/static", static_folder='./static')
app.config['CORS_HEADERS'] = 'Content-Type'

cors = CORS(app, resources={r"/foo": {"origins": "http://localhost:5000"}})

pygame.init()

# helper functions
def get_es():
	return Elasticsearch()

def get_db():
	client = MongoClient()
	db = client.podcast
	return db

def get_fs(db):
	fs = gridfs.GridFS(db)
	return fs

def delete_saved_audios():
	for f in os.listdir("static/audio_for_streaming"):
		if not f.endswith(".wav"):
			continue
		os.remove("static/audio_for_streaming/"+f)

def get_wav_file(db, name, key, nchannels, sampwidth, framerate):
	podcast_fs = get_fs(db)
	name="static/audio_for_streaming/play.wav"
	with podcast_fs.get(key) as fp_read:
		with wave.open(name, 'wb') as audio:
			audio.setnchannels(nchannels)
			audio.setsampwidth(sampwidth)
			audio.setframerate(framerate)
			audio.writeframesraw(fp_read.read())
	return "SUCCESS"



# URL mappings

# home page
@app.route('/', methods=['GET'])
@cross_origin()
def home():
	return app.send_static_file('UI.html')

#Play audio file
@app.route('/playaudio', methods=['POST'])
@cross_origin()
def playaudio():
	pygame.init()
	query = request.args.get('query')
	pygame.mixer.music.load(query.replace('"',''))
	pygame.mixer.music.play(1)
	return "SUCCESS"

# Stop playing audio
@app.route('/stopaudio', methods=['POST'])
@cross_origin()
def stopaudio():
	pygame.mixer.music.pause()
	# pygame.quit()


# search segments
@app.route('/search_podcast_segment', methods=['GET'])
@cross_origin()
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
			  "fields":  [ "title", "subtopic_name", "speaker_name", "segment_transcript"],
			  "query":     query,
			  "fuzziness": "AUTO"
			}
		  }
		})
	hits = search_result['hits']['hits']
	results = [hit['_source'] for hit in hits]
	response['response'] = results
	return response


# play audio segment
@app.route('/stream_audio', methods=['POST'])
@cross_origin()
def stream_audio():
	response = {}
	pygame.mixer.music.stop()
	pygame.quit()
	delete_saved_audios()

	query = request.args.get('query')
	query_dict = json.loads(query)[0]

	podcast_db = get_db()
	
	segment_found = list(podcast_db.segment.find({'$and':[\
		{'video_id':query_dict['video_id']},\
		{'title':query_dict['title']},\
		{'subtopic_name':query_dict['subtopic_name']},\
		{'start_timestamp':query_dict['start_timestamp']}\
		]}))

	if(len(segment_found) == 0):
		response['status'] = 'Not Found'
	else:
		gridfs_key = segment_found[0]['gridfs_key']
		nchannels = segment_found[0]['nchannels']
		sampwidth = segment_found[0]['sampwidth']
		framerate = segment_found[0]['framerate']
		filename = 'static/audio_for_streaming/'\
		+ query_dict['video_id'] + '#' \
		+ query_dict['title'] + '#' \
		+ query_dict['subtopic_name'] + '#' \
		+ query_dict['start_timestamp'] \
		+'.wav'
		response['status'] = get_wav_file(podcast_db, filename, gridfs_key, nchannels, sampwidth, framerate)
		filename = 'static/audio_for_streaming/play.wav'
		response['filename'] = filename
	return response


# search podcast metadata
@app.route('/search_podcast_metadata', methods=['GET'])
@cross_origin()
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


# search guest metadata
@app.route('/search_podcast_guest', methods=['GET'])
@cross_origin()
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


# fetch podcast entities graph
@app.route('/search_podcast_entities_graph', methods=['GET'])
@cross_origin()
def search_podcast_entities_graph():
	response = {}

	out = {}
	es_client = get_es()

	podcast = request.args.get('query')
	node_search_result = es_client.search(\
		index=[podcast+'_node_podcast'], \
		size=5000, \
		body={
		  "query": {
			"match_all": {
			}
		  }
		})
	node_hits = node_search_result['hits']['hits']
	nodes = [hit['_source'] for hit in node_hits]

	node_ids = [node['id'] for node in nodes]
	node_ids_string = ','.join(node_ids)
	edge_search_result = es_client.search(\
		index=[podcast+'_edge_podcast'], \
		size=5000, \
		body={
		  "query": {
			"match_all": {
			}
		  }
		})
	edge_hits = edge_search_result['hits']['hits']
	edges = [hit['_source'] for hit in edge_hits]

	# nodes.extend(chunk_results)
	all_nodes = [dict(t) for t in {tuple(d.items()) for d in nodes}]
	out['nodes'] = all_nodes
	out['links'] = edges
	response['response'] = out
	return response


# fetch people mentions
@app.route('/search_people_mentions', methods=['GET'])
@cross_origin()
def search_people_mentions():
	response = {}

	out = {}
	es_client = get_es()

	guest = request.args.get('query')
	node_search_result = es_client.search(\
		index=['people_graph_node'], \
		size=5000, \
		body={
		  "query": {
			"match_all": {
			}
		  }
		})
	node_hits = node_search_result['hits']['hits']
	nodes = [hit['_source'] for hit in node_hits]

	node_ids = [node['id'] for node in nodes]
	node_ids_string = ','.join(node_ids)
	edge_search_result = es_client.search(\
		index=['people_graph_edge'], \
		size=5000, \
		body={
		  "query": {
			"match_all": {
			}
		  }
		})
	edge_hits = edge_search_result['hits']['hits']
	edges = [hit['_source'] for hit in edge_hits]

	# nodes.extend(chunk_results)
	all_nodes = [dict(t) for t in {tuple(d.items()) for d in nodes}]
	out['nodes'] = all_nodes
	out['links'] = edges
	response['response'] = out
	return response


# fetch place mentions
@app.route('/search_place_mentions', methods=['GET'])
@cross_origin()
def search_place_mentions():
	response = {}

	out = {}
	es_client = get_es()

	guest = request.args.get('query')
	node_search_result = es_client.search(\
		index=['place_graph_node'], \
		size=5000, \
		body={
		  "query": {
			"match_all": {
			}
		  }
		})
	node_hits = node_search_result['hits']['hits']
	nodes = [hit['_source'] for hit in node_hits]

	node_ids = [node['id'] for node in nodes]
	node_ids_string = ','.join(node_ids)
	edge_search_result = es_client.search(\
		index=['place_graph_edge'], \
		size=5000, \
		body={
		  "query": {
			"match_all": {
			}
		  }
		})
	edge_hits = edge_search_result['hits']['hits']
	edges = [hit['_source'] for hit in edge_hits]

	# nodes.extend(chunk_results)
	all_nodes = [dict(t) for t in {tuple(d.items()) for d in nodes}]
	out['nodes'] = all_nodes
	out['links'] = edges
	response['response'] = out
	return response


# fetch book mentions
@app.route('/search_book_mentions', methods=['GET'])
@cross_origin()
def search_book_mentions():
	response = {}

	out = {}
	es_client = get_es()

	guest = request.args.get('query')
	node_search_result = es_client.search(\
		index=['book_graph_node'], \
		size=5000, \
		body={
		  "query": {
			"match_all": {
			}
		  }
		})
	node_hits = node_search_result['hits']['hits']
	nodes = [hit['_source'] for hit in node_hits]

	node_ids = [node['id'] for node in nodes]
	node_ids_string = ','.join(node_ids)
	edge_search_result = es_client.search(\
		index=['book_graph_edge'], \
		size=5000, \
		body={
		  "query": {
			"match_all": {
			}
		  }
		})
	edge_hits = edge_search_result['hits']['hits']
	edges = [hit['_source'] for hit in edge_hits]

	# nodes.extend(chunk_results)
	all_nodes = [dict(t) for t in {tuple(d.items()) for d in nodes}]
	out['nodes'] = all_nodes
	out['links'] = edges
	response['response'] = out
	return response



# execution starts here
if __name__ == '__main__':

	#stream_audio()
    app.run(host='0.0.0.0', port=5000, debug=True)
