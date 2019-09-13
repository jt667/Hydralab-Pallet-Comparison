import os
import csv
import subprocess
import sys
import tkinter

from tkinter import ttk
from itertools import compress
from tempfile import mkstemp
from shutil import move
from os import fdopen, remove, listdir
from os.path import isfile, join
from timeit import default_timer as timer

import pallet_processing
import main_processing
import raster_processing
from date_checker import date_boundary
from shader import pcv

class Error(Exception):
    """Base class for other exceptions"""
    pass

class noFirstDay(Error):
    """Raised when there is no first day to compare to"""
    pass

class invalidAnswer(Error):
    """Raised when the answer given is not of the correct format"""
    pass
