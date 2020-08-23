# Importing Required Packages
import os
import pandas as pd
import PyPDF2
import tabula

from datetime import datetime
from tabula import read_pdf
from PyPDF2 import PdfFileReader, PdfFileWriter
from flask import Flask

# Database Connection
import mysql.connector
from sqlalchemy import create_engine

# To Avoid DataFrame Warnings for Modifying existing DF
pd.options.mode.chained_assignment = None
