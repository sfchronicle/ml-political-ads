from youtube_transcript_api import YouTubeTranscriptApi
# assigning srt variable with the list
# of dictonaries obtained by the get_transcript() function
srt = YouTubeTranscriptApi.get_transcript("phLp03VtiSg")
#prints the result
for item in srt:
  print(item['text'])

