# -*- coding: utf-8 -*-
'''
Local Settings for a heroku_ebooks account. #fill in the name of the account you're tweeting from here.
'''

#configuration
DEBUG = True #Set this to False to start Tweeting live
REPLIES = True
WORDCLOUD = True

# Tweet lengths - tweak to taste.
LONGTWEET = 60
SHORTTWEET = 10
MAXTWEETLENGTH = 140
TWEETFREQUENCY = .2

DEEP = 50
SHALLOW = 12

INCLUDE_URLS = False

DEFAULTWORDFILTERLIST = u'fag(got)?|nigg(er|a)|rutt|whore|\brape|raiskau|retard|suicid(e|al)|pedophil(e|ia)'
DEFAULTWORDREPLACEWITH = u'XXXX'

#List of accounts. The format is: [[Account name],[Source(s)],[App API],[App secret],[User API],[User secret],[Word filter list],[Word censor]]

ACCOUNTS = [
	[	
		[ACCOUNT NICKNAME],
		[Twitter handle(s) to be included],
		[APP API],
		[APP SECRET],
		[USER API],
		[USER SECRET],
		[FILTERED WORD LIST],
		[STRING TO REPLACE FILTERED WORDS]
	
	]

]

COMMONWORDS = ['xd','the','be','to','of','and','don','in','that','have','i','it','for','not','on','with','he','as','you','do','at','this','but','his','by','from','they','we','say','her','she','or','an','will','my','one','all','would','there','their','what','so','up','out','if','about','who','get','which','go','me','when','make','can','like','time','no','just','him','know','take','people','into','year','your','good','some','could','them','see','other','than','then','now','look','only','come','its','over','think','also','back','after','use','two','how','our','work','first','well','way','even','new','want','because','any','these','give','day','most','us''das', 'ist', 'du', 'ich', 'nicht', 'die', 'es', 'und', 'Sie', 'der', 'was', 'wir', 'zu', 'ein', 'er', 'in', 'sie', 'mir', 'mit', 'ja', 'wie', 'den', 'auf', 'mich', 'dass','daß', 'so', 'hier', 'eine', 'wenn', 'hat', 'all', 'sind', 'von', 'dich', 'war', 'haben', 'für', 'an', 'habe', 'da', 'nein', 'bin', 'noch', 'dir', 'uns', 'sich', 'nur', 'einen', 'kann', 'dem', 'auch', 'schon', 'als', 'dann', 'ihn', 'mal', 'hast', 'sein', 'ihr', 'aus', 'um', 'aber', 'meine', 'Aber', 'wird', 'doch', 'mein', 'bist', 'im', 'keine', 'gut', 'oder', 'weiß', 'jetzt', 'man', 'nach', 'werden', 'wo', 'Oh', 'will', 'also', 'mehr', 'immer', 'muss', 'warum', 'bei', 'etwas', 'nichts', 'bitte', 'wieder', 'machen', 'diese', 'vor', 'können', 'hab', 'zum', 'gehen', 'sehr', 'geht', 'sehen']
STOPWORDS = COMMONWORDS
MASK_LIST = [LIST OF *_mask.jpg FILES IN \masks FOLDER