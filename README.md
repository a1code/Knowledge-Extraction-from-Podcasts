# Knowledge-Extraction-from-Podcasts

**Note**: Please refer Project_Description.pdf and demo_version0.1.mp4 for details.  

**Implementation Summary**:  
• Developed end-to-end data pipeline to extract, transform and index segments by speaker in Lex Fridman podcasts for creating a knowledge repository in Elasticsearch, accessible through a flask application interface  
• Implemented modules for audio segmentation, speech-to-text, text summarization, NER and knowledge graph visualization tasks by leveraging libraries such as pydub, CMUSphinx, deepspeech, spacy, PySpark and d3.js  
• Setup the data model for raw and processed data to answer user queries, and visualize the knowledge graph  

**Dataset**: [Lex Fridman Podcast](https://www.youtube.com/watch?v=S_AFc_BXht4&list=PLrAXtmErZgOdP_8GztsuKi9nrraNbKKp4)

**Requirements**:  
Java (>=1.8)  
Elasticsearch(>=7.9.1)  
MongoDB (>=3.6)  
Maven (>=3.3.9)  
Python (3+)  
PySpark (3.0.0+) 

**Deployment on localhost**:  
1) Launch Elasticsearch service.  
```
python3 -m pip install elasticsearch
sudo service elasticsearch start
curl -XGET "localhost:9200"
```
2) Launch MongoDB daemon.  
```
pip3 install pymongo
sudo service mongod start
```
3) Setup the dependencies.  
```
sudo apt update
sudo apt install ffmpeg
pip3 install pytube
pip3 install pydub
pip3 install deepspeech
curl -LO https://github.com/mozilla/DeepSpeech/releases/download/v0.6.0/deepspeech-0.6.0-models.tar.gz
tar xvf deepspeech-0.6.0-models.tar.gz
rm deepspeech-0.6.0-models.tar.gz
pip3 install transformers==2.8.0
pip3 install torch==1.4.0
pip3 install bert-extractive-summarizer
pip3 install pandas
pip3 install spacy
python3 -m spacy download en_core_web_sm
pip3 install Flask
```  
4) Run Data Ingestion Layer.  
```
python3 data_ingestion_layer/extract/data_downloader.py

python3 data_ingestion_layer/transform/data_segmentation_by_subtopics.py

cd data_ingestion_layer/transform/speaker-diarisation
mvn clean install
cd ../../..
echo $PWD
java -jar data_ingestion_layer/transform/speaker-diarisation/target/speaker-diarisation-0.0.1-jar-with-dependencies.jar "<Path from previous command>"

python3 data_ingestion_layer/transform/data_segmentation_by_speakers.py

python3 data_ingestion_layer/load/mongo_raw_data_load.py

python3 data_ingestion_layer/load/es_index_segments.py

python3 data_ingestion_layer/load/es_index_metadata_and_speakers.py
```
5) Create index on MongoDB.
```
mongo
> show dbs
> use podcast
> db.segment.createIndex({ "video_id" : 1 })
```  
5) Run Analytical Layer.  
```
spark-submit --packages "org.mongodb.spark:mongo-spark-connector_2.12:3.0.0" analytical_layer/setup_knowledge_graph.py

python3 analytical_layer/index_knowledge_graph.py
curl -XGET "localhost:9200/_cat/indices"
```  
5) Run Data Serving Layer.  
```
cd data_serving_layer
python3 podcast_explorer_app.py
```  
6) Application is deployed at ```http://localhost:8080```.
