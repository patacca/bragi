#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This program is distributed under the GPLv3 license

import logging, sqlite3, requests, re, threading

from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
from telegram.ext import MessageHandler, Filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, MessageEntity

import config


class Singleton(type):
	_instances = {}
	def __call__(cls, *args, **kwargs):
		if cls not in cls._instances:
			cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
		return cls._instances[cls]


def error(update, context):
	bot = BragiBot()
	bot.error(update, context)

def startAction(update, context):
	buttons = [
		[InlineKeyboardButton("List all", callback_data='list')]
	]
	replyMarkup = InlineKeyboardMarkup(buttons)

	update.message.reply_text('Choose one:', reply_markup=replyMarkup)

def buttonHandler(update, context):
	print(update)

def messageHandler(update, context):
	bot = BragiBot()
	bot.messageHandler(update, context)


class BragiBot(metaclass=Singleton):
	_API_URL = "https://www.googleapis.com/youtube/v3/videos?part=snippet,contentDetails&id=%s&key=%s"

	def __init__(self):
		logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
		self.logger = logging.getLogger(__name__)
		self.db = sqlite3.connect(config.DBNAME, check_same_thread=False)
		self.dbConn = self.db.cursor()
		self.token = config.TOKEN
		self.apiKey = config.API_KEY
		self.mutex = threading.Lock()

	def error(self, update, context):
		self.logger.warning('Update "%s" caused error "%s"', update, context.error)

	def formatAPI(self, url):
		r = re.search('(\?|&)v=([0-9a-zA-Z\-_]+)', url)
		if r == None:
			return ''
		return self._API_URL % (r.groups()[1], self.apiKey)

	def parseTitle(self, text):
		return (None, None, None, None)

	def messageHandler(self, update, context):
		self.logger.info('Got a url %s', update.message.text)
		url = self.formatAPI(update.message.text)
		if url == '':
			return
		r = requests.get(url)
		if not r.ok:
			return
		
		data = r.json()
		snippet = data['items'][0]['snippet']
		contentDetails = data['items'][0]['contentDetails']
		artist, album, title, year = self.parseTitle(snippet['title'])
		params = (
			update.message.text,
			snippet['publishedAt'],
			snippet['title'],
			contentDetails['duration'],
			artist,
			album,
			title,
			year
		)
		
		self.logger.info('Inserting data in the database\n\t\t(%s, %s, %s, %s, %s, %s, %s, %s)' % params)
		
		self.mutex.acquire()
		self.dbConn.execute("""
			INSERT INTO `videos`
				(full_url, published_at, full_video_title, length, artist, album, title, year)
			VALUES
				(?, ?, ?, ?, ?, ?, ?, ?)
		""", params)
		self.db.commit()
		self.mutex.release()

	def run(self):
		updater = Updater(token=self.token, use_context=True)

		dp = updater.dispatcher

		dp.add_handler(CommandHandler("start", startAction))
		dp.add_handler(CallbackQueryHandler(buttonHandler))
		dp.add_handler(MessageHandler(Filters.text & Filters.entity(MessageEntity.URL), messageHandler))
		
		dp.add_error_handler(error)

		updater.start_polling()


if __name__ == '__main__':
	bot = BragiBot()
	bot.run()
