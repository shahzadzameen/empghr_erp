# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from dotenv import load_dotenv
import os

__version__ = '0.0.1'

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(dotenv_path=os.path.join(BASE_DIR, "../",".env"))