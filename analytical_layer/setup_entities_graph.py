from pymongo import MongoClient
import spacy
import re
import pandas as pd
import os
import json


def get_db():
	client = MongoClient()
	db = client.podcast
	return db


def trim_transcript(full_text):
	sentences = []

	start_idx = full_text.find("my conversation with")
	end_idx = full_text.find("for listening to this conversation with")

	podcast_text = re.sub("[\[].*?[\]]", "", full_text[start_idx:end_idx])
	doc = nlp(podcast_text)
	for sent in doc.sents:
		sentence = sent.text.strip()
		if ("heres my conversation with" not in sentence) \
		and ("for listening to this conversation with" not in sentence) \
		and (len(sentence.split()) > 2):
			sentences.append(sentence)
	return sentences


def find_main_entities(sentence):
	doc = nlp(sentence)

	entities = []
	if doc.ents:
		for ent in doc.ents:
			if (ent.label_ not in ['CARDINAL', 'ORDINAL', 'DATE', 'TIME', 'QUANTITY']):
				entities.append(ent.text)
	return entities

def find_relations(sentence, main_entities):
	doc = nlp(sentence)

	relations = {}
	for idx, token in enumerate(doc):
		if any(item.startswith(token.text) for item in main_entities):
			matched_main_entities = [x for x in main_entities if x.startswith(token.text)]
			for main_entity in matched_main_entities:
				if(doc[idx-1].pos_ =='ADJ'):
					if (main_entity not in relations.keys()) or (not relations[main_entity]):
						relations[main_entity] = doc[idx-1].text
				else:
					if (main_entity not in relations.keys()) or (not relations[main_entity]):
						relations[main_entity] = ""

		if (not token.is_stop) and (not any(item.startswith(token.text) for item in main_entities))\
		and (token.text not in stop_phrases):
			# print(token.text + ' - ' + token.pos_ + ' - ' + token.tag_ + ' - ' + token.dep_)
			if (token.pos_ == 'NOUN'):
				if(doc[idx-1].pos_ =='ADJ'):
					if (token.text not in relations.keys()) or (not relations[token.text]):
						relations[token.text] = doc[idx-1].text
				else:
					if (token.text not in relations.keys()) or (not relations[token.text]):
						relations[token.text] = ""
	return relations

def get_named_entities(list_of_sentences):
	dict_edges = {}

	for sentence in list_of_sentences:
		# print(sentence)
		# print()
		named_entities = find_main_entities(sentence)
		relations = find_relations(sentence, named_entities)

		for key, value in relations.items():
			if (key not in dict_edges.keys()) or (not dict_edges[key]):
				dict_edges[key] = value
	
	return json.dumps(dict_edges)



# execution starts here
if __name__ == '__main__':
	nlp = spacy.load("en_core_web_sm")

	# based on observation
	stop_phrases = ["lets", "things", "time", "day", "bunch", "hour", "et cetera", "cetera", "lot", "sort", \
	"forms", "arc", "year", "month", "minute", "second", "mens", "Ill", "d", "s", "bit"]

	# get MongoDb client
	nodes_raw = []
	podcast_db = get_db()

	podcasts = [file for file in os.walk("./transcripts")][0][2]
	
	titles = podcast_db.segment.distinct("title")
	for title in titles:
		number = title.split("_")[-1]
		speaker_name = title.split("_")[0]

		speaker_name_to_find = '_'.join(speaker_name.split(' '))
		podcast_file = [podcast for podcast in podcasts if (speaker_name_to_find in podcast) and (number in podcast)]
		if len(podcast_file) > 0:
			with open("./transcripts/"+podcast_file[0], 'r') as f:
				print('Reading : ', podcast_file[0])
				transcript_raw = f.read()
				# print(transcript_raw)
				transcript_sentences = trim_transcript(transcript_raw)
				# print(transcript_sentences)
				ner = get_named_entities(transcript_sentences)
				nodes_raw.append((title, ner))

	for node in nodes_raw:
		podcast_title = node[0]
		print("Processing : ", podcast_title)
		entities = json.loads(node[1])

		all_entities = list(entities.keys())
		all_entities.append(podcast_title)

		guest = podcast_title.split("_")[0]
		
		# get all nodes for knowledge graph
		list_all_nodes = []
		all_nodes_dict = {}
		node_count = 0
		for entity in all_entities:
			dict_node = {}
			dict_node['id'] = 'n'+str(node_count)
			if entity.startswith(guest):
				group = 1
			else:
				group = 2
			dict_node['name'] = entity
			dict_node['group'] = group

			# push to dict for creating edges later
			all_nodes_dict[dict_node['name']] = dict_node['id']
			
			list_all_nodes.append(dict_node)
			node_count = node_count + 1
	
		# get all edges for knowledge graph
		src_node_id = list_all_nodes[node_count-1]['id']
		list_all_edges = []
		edge_count = 0
		for key, value in entities.items():
			if key.strip() in all_nodes_dict.keys():
				dict_edge = {}
				dict_edge['id'] = 'e'+str(edge_count)
				dict_edge['source'] = src_node_id
				dict_edge['target'] = all_nodes_dict[key.strip()]
				dict_edge['value'] = value
				
				list_all_edges.append(dict_edge)
				edge_count = edge_count + 1

		path = 'knowledge_graph/' + podcast_title
		if not os.path.exists(path):
			os.makedirs(path)

		pd.DataFrame(list_all_nodes).to_csv(path + '/nodes.csv', index=False)
		pd.DataFrame(list_all_edges).to_csv(path + '/edges.csv', index=False)