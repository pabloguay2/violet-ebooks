# -*- coding: utf-8 -*-
import random
import re
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import locale
locale.setlocale(locale.LC_ALL, '')
import twitter
import time
import markov
from htmlentitydefs import name2codepoint as n2c
from local_settings import *
from wordcloud import WordCloud

from PIL import Image
import numpy as np

def connect(account):
	api = twitter.Api(consumer_key=account[2][0],
						  consumer_secret=account[3][0],
						  access_token_key=account[4][0],
						  access_token_secret=account[5][0])
	return api

def filter_tweet(input_text, censored = True):
	tweet_text = input_text
	tweet_text = re.sub(r'\b(RT|MT) .+','',tweet_text) #take out anything after RT or MT
	tweet_text = re.sub(r'http\S+','',tweet_text) #Take out URLs
	tweet_text = re.sub(r'@[A-Za-z0-9_]+','',tweet_text) # Take out usernames
	tweet_text = re.sub(r'\n',' ', tweet_text) #take out new lines.
	# tweet_text = re.sub(r'#\S+','', tweet_text) #Take out hashtags
	# Fix some of the JSON weirdness...
	tweet_text = re.sub(r'&lt;','<',tweet_text)
	tweet_text = re.sub(r'&gt;','>',tweet_text)
	tweet_text = re.sub(r'&amp;','&',tweet_text)
	# Word filter
	if wordfilter != None and censored:
		tweet_text =  re.sub(r'(?i)'+wordfilter,wordreplacewith,tweet_text)
	if not re.search(r'([\.!?"\'*()<>\;:]$)', tweet_text):
		tweet_text+="." # Adds a period to the end if the text doesn't end in a punctuation mark
	tweet_text = re.sub(r'\.\.+',u'\u2026', tweet_text) #replaces disconnected ellipses with unicode version
	return tweet_text
	
def initialize_markov(markv, source_tweets):
	if len(source_tweets) < 2 :
		print "Unable to generate tweet: source list too short!"
		return None
	
	for tweet in source_tweets:
		markv.add_text(tweet)
		
	return markv	


def grab_tweets(api, user, depth=16, include_urls=False, censored = True):
	tweet_count = 0
	max_id = None
	source_tweets=[]
	for x in range(depth):
		try :
			user_tweets = api.GetUserTimeline(screen_name=user, count=200, max_id=max_id, include_rts=False, trim_user=True, exclude_replies=False)
		except:
			print "API error fetching tweets from " + user
			print str(tweet_count) +" tweets found in "+ user
			return source_tweets
		if user_tweets == []:
			print "No more tweets from " + user +" available (due to API limits)"
			print str(tweet_count) +" tweets found in "+ user
			return source_tweets
		max_id = user_tweets[-1].id-1
		tweet_count = len(source_tweets)
		for tweet in user_tweets:
			tweet_text = tweet.text.decode('utf-8')
			tweet_text = filter_tweet(tweet_text, censored)
			if (include_urls or len(tweet.urls) == 0) and len(tweet.text) != 0:
			#if len(tweet.text) != 0:
				source_tweets.append(tweet_text)
	
	print str(tweet_count) +" tweets found in "+ user
	if tweet_count == 0:
		print "Error fetching tweets from "+user
	return source_tweets
	
def grab_my_last_tweets (api):
	try:
		my_tweets=api.GetHomeTimeline(count = 200, trim_user=True, exclude_replies=False)
	except:
		print ("Error fetching tweets")
		raise
		return []
	if my_tweets == []:
		print("No tweets found")
		return []
	return my_tweets
	
def filter_for_relevant(filter_by, source_tweets):
	filtered_source_tweets = []
	filter_by = re.sub(r"@[A-Za-z0-9_]+","",filter_by)
	source_words = re.split(r"\W+", filter_by)
	words = []
	total_words = 0
	for word in source_words:
		if len(word) > 2:
			is_common = 0
			for c_word in COMMONWORDS:
				if re.search(r'(?i)' + word ,c_word):
					is_common += 1
			if is_common == 0:
				words.append(word.lower())
				
	for tweet in source_tweets:
		for word in words:
			if word in tweet.lower() and tweet not in filtered_source_tweets:
				filtered_source_tweets.append(tweet)
				total_words += len(re.split(r"\W+",tweet))
	
	if len(filtered_source_tweets) < 2 or total_words < 4:
		print "Not enough relevant source tweets found!"
		return source_tweets
	else:
		print "Found " + str(len(filtered_source_tweets)) + " relevant source tweets."
		return filtered_source_tweets
	
def grab_replies(api) :
	last_tweets = grab_my_last_tweets(api)
	if last_tweets == []:
		print("Error grabbing tweets")
		return []
	first_tweet = last_tweets[-1]
	last_tweet = last_tweets[0]
	first_tweet_id = first_tweet.id
	last_tweet_id = last_tweet.id
	try:
		reply_tweets_fetched = api.GetMentions(include_entities=True,  count=100)
	except:
		print("Error fetching replies")
		raise
		return []
	reply_tweets = []
	for tweet in reply_tweets_fetched:
		replies_count_me = 0
		replies_count_others = 0
		for other_tweet in reply_tweets_fetched:
			if tweet.id == other_tweet.in_reply_to_status_id:
				replies_count_others += 1
		for other_tweet in last_tweets:
			if tweet.id == other_tweet.in_reply_to_status_id:
				replies_count_me += 1	
		if (replies_count_me == 0 and tweet.id > first_tweet_id) and (replies_count_others == 0 or re.search(r"#wordcloud",tweet.text.lower())):
			reply_tweets.append(tweet)

	return reply_tweets

def generate_reply_tweets(source_tweets, reply_tweets = []) :
	if reply_tweets == []:
		reply_tweets = grab_replies(api)
	for tweet in reply_tweets:
		if re.search('#wordcloud',tweet.text.lower()) and WORDCLOUD:
			reply_to_user=tweet.user.screen_name
			masks_re = r"random"
			for mask_shape in MASK_LIST:
				masks_re = masks_re + "|"+ mask_shape
			try:
				shape = re.search(masks_re,re.sub(u"@[A-Za-z0-9_]+","",tweet.text.lower())).group(0)
			except:
				shape = None
			if len(re.findall(u"@[A-Za-z0-9_]+",tweet.text))>1:
				mentioned_users_read = re.findall(r'@[A-Za-z0-9_]+',tweet.text)
				for i in range(len(mentioned_users_read)):
					if reply_to_user.lower() not in mentioned_users_read[i].lower() and MY_ACCOUNT.lower() not in mentioned_users_read[i].lower() :
						wordcloud_user = (mentioned_users_read[i][1:])
						break
				
			else:
				wordcloud_user = tweet.user.screen_name
			print ("Generating wordcloud in response to the tweet: " + tweet.text)
			make_wordcloud(reply_to_user, wordcloud_user, tweet.id, shape)
		elif REPLIES:
			print ("Generating tweet in reply to " + tweet.user.screen_name + ": " + tweet.text.encode('ascii', errors='replace'))
			if tweet.user.screen_name in BOT_LIST:
				print ("Skipping reply to bot account")
			else:
				reply_to_user = tweet.user.screen_name
				mentioned_users_read = re.findall(r'@[A-Za-z0-9_]+',tweet.text)
				mentioned_users = []
				for i in range(len(mentioned_users_read)):
					if reply_to_user.lower() != mentioned_users_read[i].lower()[1:] and MY_ACCOUNT.lower() != mentioned_users_read[i].lower()[1:] :
						mentioned_users.append (mentioned_users_read[i][1:])
								
				reply_to_id = tweet.id
				
				reply_source_tweets = filter_for_relevant(tweet.text, source_tweets)
				
				reply_tweet = generate_tweet(reply_source_tweets, "short", reply_to_user, reply_to_id, mentioned_users)
			
				
		
def generate_tweet(source_tweets, length="long", reply_to_user=None, reply_to_id = None, mentioned_users=None):
	
	mMarkov = markov.MarkovChainer(2)
	if initialize_markov(mMarkov, source_tweets) == None:
		return ""
	
	if length == "short" :
		mintweetlength = SHORTTWEET
	else:
		mintweetlength = LONGTWEET
	# print(source_tweets)
	tweet_text = generate_fragment(mMarkov)

	#if a tweet is very short, this will randomly add a second sentence to it.
	while len(tweet_text) < mintweetlength:
		newer_tweet = tweet_text + " " + generate_fragment(mMarkov)
		if len(newer_tweet) < MAXTWEETLENGTH:
			tweet_text = newer_tweet
		
	#throw out tweets that match anything from the source account.
	
	for user_tweet in source_tweets:
		if tweet_text[:-1] in filter_tweet(user_tweet):
			add_text = generate_fragment(mMarkov)
			if add_text.lower()[:-1] != tweet_text[:-1].lower():
				tweet_text = tweet_text + " " + add_text
	
	if tweet_text == None:
		print "Tweet is empty, sorry."
		return ""
	
	if reply_to_user != None and reply_to_id != None:
		reply_text = u"@"+reply_to_user+u" "
		for user in mentioned_users:
			reply_text = reply_text + u"@"+user+u" "
		tweet_text = reply_text + tweet_text
		
	if len(tweet_text) >= MAXTWEETLENGTH:
		tweet_text = tweet_text[:MAXTWEETLENGTH-1] + u"\u2026"
		
	post_tweet(tweet_text, reply_to_id)
	return tweet_text
	
def post_tweet (tweet_text, reply_to_id = None, attachment = None):
	if DEBUG == False:
		try:
			status = api.PostUpdate(tweet_text, media= attachment, in_reply_to_status_id=reply_to_id)
			print status.text.encode('ascii', errors='replace')
		except:
			print u"Error posting tweet: " + tweet_text.encode('ascii', errors='replace')
			raise
	else:
		print u"Generated tweet (DEBUG): " + tweet_text.encode('ascii', errors='replace')

def generate_fragment (mMarkov):
	fragment = mMarkov.generate_sentence()
	if re.search(r"\"", fragment):
		fragment = u"\"" + fragment
	if re.search(r"\*",fragment):
		fragment = u"*" + fragment
	if re.search(r"\)", fragment) and not re.search(r"[:;\(]",fragment):
		fragment = u"(" + fragment
	if re.search(r"\(", fragment) and not re.search(r"[:;\)]",fragment):
		fragment = fragment + u")"
	
	return fragment
	
def read_common_words():
	
	file_str = 'assets/stopwords-{0}.txt'
	langs = ['de', 'en', 'es', 'fr', 'it']
	for l in langs:
		
		with open(file_str.format(l), 'r') as f:
			for line in f.readlines():
				STOPWORDS.append(re.sub(u"\n","",line))
	return STOPWORDS
	
def make_wordcloud(twitter_user, wordcloud_user, reply_to_id, shape=None):
	""" Build the word cloud png image of a twitter user
	:param twitter_user: name of the twitter account (string)
	:return: path to the word cloud image (string),
			 None if an error occurs or there are no words to build the word cloud
	"""
	print "Generating wordcloud for " + wordcloud_user
	user_tweets = []
	words = []
	mymask = None
	
	try:
		user_tweets.extend(grab_tweets(api, wordcloud_user, depth=SHALLOW, include_urls=False, censored = False))
	except:
		print("Couldn't get tweets!")
		post_tweet("@" + twitter_user + " sorry, there was a problem generating your wordcloud. I couldn't find that user.", reply_to_id)
		return None
	if user_tweets == []:
		print("No tweets!")
		post_tweet("@" + twitter_user + " sorry, there was a problem generating your wordcloud. I couldn't find any tweets.", reply_to_id)
		return None
	
	for tweet in user_tweets:
		tweet_words = re.split(u"\s+",tweet)
		for word in tweet_words:
			
			if re.sub(u"\W","",word.lower()) not in STOPWORDS and len(re.sub(u"\W","",word)) >= 3:
				words.append(word)
					
	if words == []:
		print("No words!")
		post_tweet("@" + twitter_user + " sorry, there was a problem generating your wordcloud. No words found", reply_to_id )
		return None
	
	try:
		print ("Creating wordcloud")
		if shape != None:
			if shape == "random":
				shape = MASK_LIST[random.choice(range(len(MASK_LIST)))]
			print ("Shape: " + shape)
			mymask = np.array(Image.open("masks/"+shape+"_mask.jpg"))
		wordcloud = WordCloud(width=1280, height=960, max_words = 120, mask=mymask, random_state = 2, background_color="black").generate(' '.join(words))
	except:
		print("Unexpected error:", sys.exc_info()[0])
		post_tweet("@" + twitter_user + " sorry, there was a problem generating your wordcloud.", reply_to_id )
		raise
		return None
	ts = str(int(time.time()))
	img_file = ts + twitter_user + ".png"
	wordcloud.to_file(img_file)
	if shape == None:
		if wordcloud_user  == twitter_user:
			post_tweet("@" + twitter_user + " here's your wordcloud: ", reply_to_id, img_file)
		else:
			post_tweet("@" + twitter_user + " here's your wordcloud for @"+wordcloud_user+": ", reply_to_id, img_file)
	else:
		if wordcloud_user  == twitter_user:
			post_tweet("@" + twitter_user + " here's your " + shape + " wordcloud: ", reply_to_id, img_file)
		else:
			post_tweet("@" + twitter_user + " here's your " + shape + " wordcloud for @"+wordcloud_user+": ", reply_to_id, img_file)
	
if __name__=="__main__":
	BOT_LIST = []
	my_tweets = []
	read_common_words()
	print("Initializing eBooks")
	# if random.random() <= 0.05 and DEBUG == False:
		# REPLIES = False
		# print "Skipping replies this cycle"
		
	for account in ACCOUNTS :
		source_tweets = []
		
		wordfilter = account[6][0]
		wordreplacewith = account[7][0]
		
		try:
			api=connect(account)
			MY_ACCOUNT = api.VerifyCredentials().screen_name
			BOT_LIST.append(MY_ACCOUNT) 
		except:
			print "Error connecting to API for " + account[0][0]
			continue
		if len(account[1]) > 3 or DEBUG:
			depth = SHALLOW
		else:
			depth = DEEP
		
		reply_tweets = grab_replies(api)
		
		tweet_this_time = random.random() < TWEETFREQUENCY
		
		if tweet_this_time or DEBUG or reply_tweets != []:
			print "Generating post for account " + account[0][0]
			if source_tweets == []:
				for handle in account[1]:
					source_tweets.extend(grab_tweets(api, handle, depth, INCLUDE_URLS))
			print str(len(source_tweets)) + " total tweets found. Generating tweet(s)..."
			
			
			generate_reply_tweets(source_tweets, reply_tweets)
			
			if tweet_this_time or DEBUG:
				tweet_text=generate_tweet(source_tweets, "long")
		else:
			print "Skipping post this cycle for account " + account[0][0]
			