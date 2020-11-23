from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import spacy
import re
import pandas as pd
import os


def create_session():
	spark = SparkSession \
	.builder \
	.appName("Named Entity Recognition from segments") \
	.config("spark.mongodb.input.uri", "mongodb://127.0.0.1/podcast.segment") \
	.getOrCreate()
	return spark


def stop_session(session):
	session.stop()


def read_from_mongo(session):
	df = session.read.format("com.mongodb.spark.sql.DefaultSource")\
	.load()
	return df

def get_named_entities(text):
	# remove stop words
	doc = nlp(text)
	clean_token = []
	for token in doc:
		if not (token.is_stop):
			clean_token.append(token.text)
	doc = nlp(' '.join(clean_token))

	# find named entities
	entities = [ent.text for ent in doc.ents]
	# if len(entities) > 0: # only for debugging purposes
	# 	print(','.join(list(set(entities))), file=open("output1.txt", "a"))
	return ','.join(list(set(entities)))


# execution starts here
if __name__ == '__main__':
	spark_session = create_session()
	udf_ner = udf(get_named_entities, StringType())


	nlp = spacy.load("en_core_web_sm")
	

	df_raw = read_from_mongo(spark_session).repartition(100)
	df_ner = df_raw \
	.withColumn('named_entities', udf_ner(col('raw_text'))).filter(col('named_entities') != '') \
	.select('speaker_name', 'named_entities') \
	.withColumn('speaker_name', concat(lit("speaker_"), col("speaker_name")))

	df_out = df_ner \
	.groupby("speaker_name") \
	.agg(concat_ws(", ", collect_list(col("named_entities"))).alias("entities"))


	# get all nodes for knowledge graph
	entities_raw = df_out.select(concat(col("speaker_name"), lit(","), col("entities")))\
	.dropDuplicates().rdd.flatMap(lambda x: x).collect()
	entities = [entity.split(",") for entity in entities_raw]
	nodes = [item.strip() for sublist in entities for item in sublist]

	list_all_nodes = []
	all_nodes_dict = {}
	node_count = 0
	for entity in nodes:
		# print(entity, file=open("output2.txt", "a")) # only for debugging purposes
		dict_node = {}
		dict_node['id'] = 'n'+str(node_count)
		dict_node['name'] = entity
		# color speaker names and keywords differently
		if entity.startswith('speaker_'):
			group = 1
		else:
			group = 2
		dict_node['group'] = group
		
		# push to dict for creating edges later
		all_nodes_dict[dict_node['name']] = dict_node['id']
		
		list_all_nodes.append(dict_node)
		node_count = node_count + 1

	
	# get all edges for knowledge graph
	speaker_vs_entities = df_out.select("speaker_name", "entities")\
	.dropDuplicates().rdd.map(lambda x: [x[0], x[1]]).collect()
	list_all_edges = []
	edge_count = 0
	for entry in speaker_vs_entities:
		for entity in entry[1].split(','):
			# print((entry, entity), file=open("output3.txt", "a")) # only for debugging purposes
			dict_edge = {}
			dict_edge['id'] = 'e'+str(edge_count)
			dict_edge['source'] = all_nodes_dict[entry[0]]
			dict_edge['target'] = all_nodes_dict[entity.strip()]
			dict_edge['value'] = 1
			
			list_all_edges.append(dict_edge)
			edge_count = edge_count + 1


	if not os.path.exists('knowledge_graph'):
		os.makedirs('knowledge_graph')

	pd.DataFrame(list_all_nodes).to_csv('knowledge_graph/nodes.csv', index=False)
	pd.DataFrame(list_all_edges).to_csv('knowledge_graph/edges.csv', index=False)

	stop_session(spark_session)