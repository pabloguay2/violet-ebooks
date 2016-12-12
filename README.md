# violet_ebooks

This is an implementation of an eBooks-style Markov chain twitter bot. It was based on [Tom Meagher's Python Port](https://github.com/tommeagher/heroku_ebooks) of [@harrisj's](https://twitter.com/harrisj) [iron_ebooks](https://github.com/harrisj/iron_ebooks/) Ruby script. 

Using Heroku's scheduler, you can post to an _ebooks Twitter account based on the corpus of an existing Twitter at regular intervals. See it in action at [@Jontron_txt](https://twitter.com/Jontron_txt), among others.

## Setup

1. Clone this repo
2. Create a Twitter account that you will post to.
3. Sign into https://dev.twitter.com/apps with the same login and create an application. Make sure that your application has read and write permissions to make POST requests.
4. Make a copy of the `local_settings_example.py` file and name it `local_settings.py`
5. Take the consumer key (and secret) and access token (and secret) from your Twiter application and paste them into the appropriate spots in `local_settings.py`. You'll also need to create a user key and secret from the "Keys and Tokens" menu in the Twitter app manager.
6. In `local_settings.py`, be sure to add the handle of the Twitter user you want your _ebooks account to be based on. To make your tweets go live, change the `DEBUG` variable to `False`.
7. Create an account at Heroku, if you don't already have one. [Install the Heroku toolbelt](https://devcenter.heroku.com/articles/quickstart#step-2-install-the-heroku-toolbelt) and set your Heroku login on the command line.
8. Type the command `heroku create` to generate the _ebooks Python app on the platform that you can schedule.
9. The only Python requirement for this script is [python-twitter](https://github.com/bear/python-twitter), the `pip install` of which is handled by Heroku automatically.
9. `git commit -am 'updated the local_settings.py'` (or whatever comment you like)
10. `git push heroku master`
11. Test your upload by typing `heroku run worker`. You should a message with the body of your post. If you get the latter, check your _ebooks Twitter account to see if it worked. If you get a timeout error, try using "heroku run:detached worker" instead. To see the console output, select "view logs" from the heroku dashboard (the three dots on the top right), or follow the console commands Heroku returns. 
12. Now it's time to configure the scheduler. `heroku addons:create scheduler:standard`, or add it from the heroku dashboard.
13. Once that runs, type `heroku addons:open scheduler`. This will open up a browser window where you can adjust the time interval for the script to run. I recommend setting it at one hour.
14. Sit back and enjoy the fruits of your labor.

(Note that you can also run this from a local server, if you like. Heroku is just a nice cloud-based alternative.)

## Configuring

There are several parameters that control the behavior of the bot. You can adjust them by setting them in your `local_settings.py` file. 

DEBUG: Set this to `True` if you just want to test something, otherwise set it to `False` to go live.

REPLIES: Determines whether you want your bot to reply to tweets sent to it.

LONG/SHORTTWEET: Sets the minimum lengths for long (regular) and short (reply) tweets.

DEEP/SHALLOW: Determines how many pages back in time you want to pull tweets from. Each page is an API hit, so setting this too high might result in overstepping your limits. (SHALLOW is used for Debug sessions and if you draw from more than three accounts)

DEFAULTWORDFILTERLIST: A regular expression that will filter out "bad" words you don't want to have show up in your eBooks account. Set to "None" for an uncensored feed.

DEFAULTWORDREPLACEWITH: What you want filtered words to show up as.

## Setting up accounts

Accounts are set up as a list of tuples, seperated by a comma. 

What goes where should be fairly self-explanatory. You can extend or replace the default word filter here as well.

## How it works

Markov chain bots basically function by finding "chunks" of words that match over all the source tweets. By default, these chunks are 2 words long, as that seems to return the most interesting and coherent responses.

For example, a tweet that begins with "I went to work today" might get matched with another that says "work today is boring", for a result that says "I went to work today is boring".

This bot skips tweets with URLs embedded when finding source tweets. That includes tweets with images, quoted tweets, etc. It will also skip retweets, but not replies. it also keeps hastags, though the spot where that can be disabled is commented out in the source code.

When replying, the bot will only reply to the most recent comment in a reply chain to avoid spam. Replies tend to be shorter than original tweets. To avoid bot reply loops, there are a few failsafes: The bot won't reply to obvious bot accounts, to accounts in the list of accounts in this app, and every once in a while it will skip replies alotgether.

If you still get caught in a bot reply loop, run the app once with replies disabled, or block the offending account in Twitter.

## Credit
The basis for this app, and the Markov algorithm, were taken from [Tom Meagher's Python Port](https://github.com/tommeagher/heroku_ebooks) of [@harrisj's](https://twitter.com/harrisj) [iron_ebooks](https://github.com/harrisj/iron_ebooks/) Ruby script. 

Most of the app itself has been rewritten by myself, but the algorithm and basic idea stem from there.

You can find me at [@ViTheDeer](http://twitter.com/ViTheDeer) if you have any questions regarding my implementation, or any suggestions for future features.