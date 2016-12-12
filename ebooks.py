# -*- coding: utf-8 -*-
import random
import re
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import locale
locale.setlocale(locale.LC_ALL, 'de_DE.UTF-8')
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

def filter_tweet(input_text):
	tweet_text = input_text
	tweet_text = re.sub(r'\b(RT|MT) .+','',tweet_text) #take out anything after RT or MT
	tweet_text = re.sub(r'http\S+','',tweet_text) #Take out URLs
	tweet_text = re.sub(r'@\S+','',tweet_text) # Take out usernames
	tweet_text = re.sub(r'\n',' ', tweet_text) #take out new lines.
	# tweet_text = re.sub(r'#\S+','', tweet_text) #Take out hashtags
	# Fix some of the JSON weirdness...
	tweet_text = re.sub(r'&lt;','<',tweet_text)
	tweet_text = re.sub(r'&gt;','>',tweet_text)
	tweet_text = re.sub(r'&amp;','&',tweet_text)
	# Word filter
	if wordfilter != None:
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


def grab_tweets(api, user, depth=16, include_urls=False):
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
			tweet_text = filter_tweet(tweet_text)
			if (include_urls or len(tweet.urls) == 0) and len(tweet.text) != 0:
			#if len(tweet.text) != 0:
				source_tweets.append(tweet_text)
	
	print str(tweet_count) +" tweets found in "+ user
	if tweet_count == 0:
		print "Error fetching tweets from "+user
	return source_tweets
	
def grab_last_tweets (api):
	
	try:
		my_tweets=api.GetUserTimeline(screen_name=MY_ACCOUNT, count=10, include_rts=False, trim_user=True, exclude_replies=False)
	except:
		return []
	if my_tweets == []:
		return []
	return my_tweets
	
def filter_for_relevant(filter_by, source_tweets):
	filtered_source_tweets = []
	filter_by = re.sub(r"@\S+","",filter_by)
	source_words = re.split(r"\W+", filter_by)
	words = []
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
	
	if len(filtered_source_tweets) < 2:
		print "Not enough relevant source tweets found!"
		return source_tweets
	else:
		print "Found " + str(len(filtered_source_tweets)) + " relevant source tweets."
		return filtered_source_tweets
	
def grab_replies(api) :
	last_tweets = grab_last_tweets(api)
	if last_tweets == []:
		return []
	else:
		last_tweet = last_tweets[0]
	last_tweet_ID = last_tweet.id
	try:
		reply_tweets_fetched = api.GetSearch(term="-from:"+MY_ACCOUNT+" @"+MY_ACCOUNT+" -RT", since_id=last_tweet_ID, include_entities=True, result_type="recent", count=100)
	except:
		return []
	reply_tweets = []
	for tweet in reply_tweets_fetched:
		replies_count = 0
		#if re.search(r'bot\b|ebooks\b',tweet.user.screen_name):
		#	continue
		for other_tweet in reply_tweets_fetched:
			if tweet.id == other_tweet.in_reply_to_status_id:
				replies_count += 1
		if replies_count == 0:
			reply_tweets.append(tweet)

	return reply_tweets

def generate_reply_tweets(source_tweets, reply_tweets = []) :
	if reply_tweets == []:
		reply_tweets = grab_replies(api)
	for tweet in reply_tweets:
		if re.search('#wordcloud',tweet.text ):
			try:
				shape = re.search(u'pony|star|heart|snowflake|deer|cat|fox|bird|fairy|xmas|chrysalis|bunny|yuri|weepingangel|wolf|cake',tweet.text).group(0)
			except:
				shape = None
				
			make_wordcloud(tweet.user.screen_name, tweet.id, shape)
		else:	
			print tweet.text.encode('ascii', errors='replace')
			if not tweet.user.screen_name in user_list:
				reply_to_user = tweet.user.screen_name
				mentioned_users_read = re.findall(r'@\S+',tweet.text)
				mentioned_users = []
				for i in range(len(mentioned_users_read)):
					if reply_to_user.lower() not in mentioned_users_read[i].lower() and MY_ACCOUNT.lower() not in mentioned_users_read[i].lower() :
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
			if add_text.lower() != tweet_text[:-1].lower():
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
	
def make_wordcloud(twitter_user, reply_to_id, shape=None):
	""" Build the word cloud png image of a twitter user
	:param twitter_user: name of the twitter account (string)
	:return: path to the word cloud image (string),
			 None if an error occurs or there are no words to build the word cloud
	"""
	print "Generating wordcloud for " + twitter_user
	user_tweets = []
	words = []
	
	try:
		user_tweets.extend(grab_tweets(api, twitter_user, depth=SHALLOW, include_urls=False))
	except:
		print("Couldn't get tweets!")
		return None
	if user_tweets == []:
		print("No tweets!")
		return None
	
	for tweet in user_tweets:
		tweet_text = filter_tweet(tweet)
		#tweet_text = re.sub(u"[.!?*\"\u2026]","",tweet_text)
		tweet_words = re.split(u"\s+",tweet_text)
		for word in tweet_words:
			
			if re.sub(u"\W","",word.lower()) not in STOPWORDS and len(re.sub(u"\W","",word)) >= 3:
				words.append(word)
					
	if words == []:
		print("No words!")
		return None
	
	try:
		print ("Creating wordcloud")
		if shape != None:
			shape = np.array(Image.open(shape+"_mask.jpg"))
		wordcloud = WordCloud(width=1280, height=960, max_words = 120, mask=shape, random_state = 2, background_color="black").generate(' '.join(words))
	except:
		print("Unexpected error:", sys.exc_info()[0])
		raise
		return None
	ts = str(int(time.time()))
	img_file = ts + twitter_user + ".png"
	
	wordcloud.to_file(img_file)
	post_tweet("@" + twitter_user + " here's your wordcloud: ", reply_to_id, img_file)
	
if __name__=="__main__":
	user_list = []
	my_tweets = []
	read_common_words()
	if random.random() <= 0.05 and DEBUG == False:
		REPLIES = False
		print "Skipping replies this cycle"
	for account in ACCOUNTS :
		source_tweets = []
		
		wordfilter = account[6][0]
		wordreplacewith = account[7][0]
		
		try:
			api=connect(account)
			MY_ACCOUNT = api.VerifyCredentials().screen_name
			user_list.append(MY_ACCOUNT) 
		except:
			print "Error connecting to API for " + account[0][0]
			continue
		if len(account[1]) > 3 or DEBUG:
			depth = SHALLOW
		else:
			depth = DEEP
		
		reply_tweets = []
		for handle in account[1]:
			reply_tweets.extend(grab_replies(api))
		
		tweet_this_time = random.random() < TWEETFREQUENCY
		
		if tweet_this_time or DEBUG or reply_tweets != []:
			print "Generating post for account " + account[0][0]
			for handle in account[1]:
				source_tweets.extend(grab_tweets(api, handle, depth, INCLUDE_URLS))
			print str(len(source_tweets)) + " total tweets found. Generating tweet(s)..."
			
			
			if REPLIES:
				generate_reply_tweets(source_tweets, reply_tweets)
			
			if tweet_this_time or DEBUG:
				tweet_text=generate_tweet(source_tweets, "long")
		else:
			print "Skipping post this cycle for account " + account[0][0]
			