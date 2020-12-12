from pydub import AudioSegment
import ast
import os


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
	# find all podcast directories
	podcasts = [x[0] for x in os.walk(".") if "podcast_" in x[0]]
	for podcast in podcasts:
		for file in os.listdir(podcast):
			# find podcast audio file in this directory
			if file.endswith(".wav"):
				print('Processing file : ', file)

				filename = file.split(".")[0]

				# read wav audio file for this podcast
				audio = AudioSegment.from_wav(podcast+'/'+file)

				# read metadata for this podcast
				with open(podcast+'/'+filename+".txt", "r") as metadata:
					dict_metadata = ast.literal_eval(metadata.read())
					desc_start_idx = dict_metadata['description'].find("OUTLINE:")
					desc_end_idx = dict_metadata['description'][desc_start_idx+8:].find("\n\n")
					video_id = dict_metadata['video_id']
					segments = dict_metadata['description'][desc_start_idx+8:desc_start_idx+8+desc_end_idx]\
						.strip().split('\n')[1:]
						
					# parse timestamp segmentation of subtopics from podcast description
					seg_start = [get_total_seconds(x.split('-')[0].strip()) for x in segments]
					seg_end = seg_start[1:]
					seg_end.append('EOF')
					subtopic = [x.split('-')[1].strip() for x in segments]
					all_segments = list(zip(seg_start, seg_end, subtopic))

				# split wav file by subtopics
				snippet_cnt = 1
				for seg in all_segments:
					# print(seg)
					if seg[1] == 'EOF':
						audio_chunk=audio[seg[0]*1000:]
					else:
						audio_chunk=audio[seg[0]*1000:seg[1]*1000] #pydub works in millisec
					
					# write each split to the directory for this podcast
					audio_chunk.export(podcast+'/'\
						+video_id+"#"\
						+seg[2]\
						+"("+str(snippet_cnt)+" of "+str(len(all_segments))+")#"\
						+str(seg[0])\
						+".wav", format="wav")
					snippet_cnt = snippet_cnt + 1

				# delete original full wav file
				delete_file_from_path(podcast+'/'+file)


# execution starts here 
if __name__=="__main__": 
	main() 