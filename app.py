# Importing Required Packages
import os
import pandas as pd
import PyPDF2
import tabula

from datetime import datetime
from tabula import read_pdf
from PyPDF2 import PdfFileReader, PdfFileWriter
from flask import Flask, flash, request, redirect, url_for, render_template, send_file

# Database Connection
import mysql.connector
from sqlalchemy import create_engine

# To Avoid DataFrame Warnings for Modifying existing DF
pd.options.mode.chained_assignment = None

# Defining UPLOAD and DOWNLOAD Folder
UPLOAD_FOLDER = os.path.dirname(os.path.abspath(__file__)) + '/uploads/'
DOWNLOAD_FOLDER = os.path.dirname(os.path.abspath(__file__)) + '/downloads/'
ALLOWED_EXTENSIONS = {'pdf'}

app = Flask(__name__)
app.secret_key = "secret key"
DIR_PATH = os.path.dirname(os.path.realpath(__file__))
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER


# Defining Allowed File Extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Main function that extracts and converts AWS Inovice PDF
