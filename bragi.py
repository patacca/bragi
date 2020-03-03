#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This program is distributed under the GPLv3 license

import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import config


if __name__ == '__main__':
	updater = Updater(config.__TOKEN, use_context=True)
