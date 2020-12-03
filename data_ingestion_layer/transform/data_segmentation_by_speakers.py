from pydub import AudioSegment
import ast
import os
import datetime as dt


def get_total_seconds(time_str):
	h, m, s = 0, 0, 0
	hms_str = time_str.split(':')
	if len(hms_str)==3:
		h = hms_str[0]
		m = hms_str[1]
		s = hms_str[2]
	if len(hms_str)==2:
		m = hms_str[0]
		s = hms_str[1]
	if len(hms_str)==1:
		s = hms_str[0]
	return int(h) * 3600 + int(m) * 60 + int(s)


def delete_file_from_path(path):
	try:
		os.remove(path)
	except OSError as e:
		print("Error: %s : %s" % (path, e.strerror))



# Main function 
def main():
	metadata_files = {}
	speaker_split_files = {}

	# find all podcast directories
	podcasts = [x[0] for x in os.walk(".") if "podcast_" in x[0]]
	for podcast in podcasts:
		# find metadata file for this podcast
		metadata_files[podcast] = [file for file in os.listdir(podcast) \
		if file.endswith(".txt") and "speakerSplits" not in file][0]

		# find subtopic speaker split files for this podcast in order
		speaker_split_files[podcast] = sorted([file for file in os.listdir(podcast) \
			if file.endswith("speakerSplits.txt")],\
			key=lambda x:\
			int(x.split("#")[1][x.split("#")[1].find("(")+1 : x.split("#")[1].find(")")].split(" ")[0]))
		
	# iterate over each podcast
	for key, value in metadata_files.items():
		# os.makedirs(key+'/temp', exist_ok=True) # only for debugging, to be removed

		# read metadata for this podcast
		with open(key+'/'+value, "r") as metadata:
			dict_metadata = ast.literal_eval(metadata.read())
			host = 'Lex Fridman'
			guest = dict_metadata['title'].split("_")[0].strip()

		speaker_iterator = [host, guest]
		
		speaker_segments = speaker_split_files[key]
		# iterate over each speaker segment for this podcast
		for file in speaker_segments:
			print('Processing file : ', file)
			min_speaker_code = -1
			video_id = file.split("#")[0]
			subtopic = file.split("#")[1]				
			start_timestamp = file.split("#")[2]

			# read wav audio file for this segment
			audio = AudioSegment.from_wav(key+'/'+video_id+'#'+subtopic+'#'+start_timestamp+'.wav')

			# parse speaker split info for this segment
			with open(key+'/'+file, "r") as speaker_splits:
				speaker_info = speaker_splits.readlines()
				subtopic_by_speakers = [(x.split('\t')[1], \
						x.split('\t')[2], \
						int(x.split('\t')[3].strip('\n'))) \
					for x in speaker_info]
				all_speaker_segments = [(get_total_seconds(x[0]), \
						get_total_seconds(x[0]) + get_total_seconds(x[1]), \
						x[2]) \
					for x in subtopic_by_speakers]

				# split wav file by speaker segments
				snippet_count = 0
				for speaker_segment in all_speaker_segments:
					snippet_count = snippet_count + 1
					snippet = "(" + str(snippet_count) + " of " + str(len(all_speaker_segments)) + ")"
					# print(speaker_segment)

					audio_chunk=audio[speaker_segment[0]*1000:speaker_segment[1]*1000] #pydub works in millisec
					
					# get speaker for this segment; tricky part, not too accurate currently, improve this later
					if (min_speaker_code == -1) or (speaker_segment[2] < min_speaker_code):
						min_speaker_code = speaker_segment[2]
						speaker = speaker_iterator[0]
					elif (min_speaker_code - speaker_segment[2]) == 0:
						speaker = speaker_iterator[0]
					else:
						speaker = speaker_iterator[1]

					# write each split to the directory for this podcast
					audio_chunk.export(\
						key+'/'\
						+video_id+"#"\
						+subtopic+"#"\
						+speaker+snippet+"#"\
						+str(int(start_timestamp) + speaker_segment[0])+"#"\
						+str(int(start_timestamp) + speaker_segment[1])+"#"\
						+".wav", format="wav")
			
			# delete speaker split info txt file and input wav file
			delete_file_from_path(key+'/'+file)
			delete_file_from_path(key+'/'+video_id+'#'+subtopic+'#'+start_timestamp+'.wav')


# execution starts here 
if __name__=="__main__": 
	main() 