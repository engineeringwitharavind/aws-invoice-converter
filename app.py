# Importing Required Packages
import os
import io
import pandas as pd
import PyPDF2
import tabula
import dotenv

from datetime import datetime
from tabula import read_pdf
from PyPDF2 import PdfFileReader, PdfFileWriter
from flask import Flask, flash, request, redirect, url_for, render_template, send_file
from werkzeug.utils import secure_filename
from io import StringIO
from io import BytesIO

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
def AWS_CM():
    # Initalizing list of files and filenames
    files = os.listdir(UPLOAD_FOLDER)
    fileList = []
    fileName = []
    for filename in files:
        fileList.append(UPLOAD_FOLDER + filename)
        fileName.append(filename)

    accountNumber = []  # DONE
    billingPeriod = []  # DONE
    invoiceCurrency = []  # DONE
    creditMemoCurrency = []  # DONE

    for index in range(len(fileList)):
        text = ""
        pdfFileObj = open(fileList[index], 'rb')
        pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
        # for page in range(pdfReader.numPages):
        pageObj = pdfReader.getPage(0)
        text = text + pageObj.extractText()

        # File Name
        inputFile = filename

        # Account Number
        text = text.replace("\n", "")
        c = (text.find("ACCOUNT ID #") + len("ACCOUNT ID #"))
        accountNumber.append(text[c:c+12])

        # Billing Period
        c = text.find(" billing period ")
        if (c != -1):
            c = text.find(" billing period ") + len(" billing period ")
            billingPeriod.append(text[c:c+20])

        # Usage Details Data
        tabula.convert_into(
            fileList[index], "test.csv", output_format="csv", pages=1, stream=True, guess=False)
        df = pd.read_csv("test.csv", header=None)
        df.columns = ['Description', 'Amount']
        startRow = df[df['Description'] == 'Usage Detail'].index.tolist()[0]
        endRow = df[df['Description'] == 'Total Amount Outstanding'].index.tolist()[
            1]

        # Extracting Usage Details Table from whole DataFrame
        mainDF = df.iloc[startRow+2:endRow-1]

        # Invoice Currency
        currency = []
        if mainDF['Amount'].str.contains('INR').any():
            mainDF['Amount'] = mainDF['Amount'].str.replace("INR", "")
            currency = 'INR'
        elif mainDF['Amount'].str.contains('USD').any():
            mainDF['Amount'] = mainDF['Amount'].str.replace("USD", "")
            currency = 'USD'
        else:
            currency = 'N/A'
        invoiceCurrency.append(currency)
        creditMemoCurrency.append(currency)

        # Extracting Description and Invoice Number seperately
        mainDF[['Description', 'Invoice Number']] = mainDF.Description.apply(
            lambda x: pd.Series(str(x).split("#")))
        mainDF['Amount'] = mainDF['Amount'].replace(
            to_replace='\(', value="", regex=True).replace(to_replace='\)', value="", regex=True)

        dataDF = mainDF[mainDF.columns[[0, 2, 1]]]

        DF1 = dataDF[dataDF['Description'].str.contains("Invoice")]
        invoiceDF = DF1.rename(
            columns={'Description': 'Invoice Description', 'Amount': 'Invoice Value'})

        DF2 = dataDF[dataDF['Description'].str.contains("Credit Memo")]
        creditDF = DF2.rename(columns={'Description': 'Credit Memo Description',
                                       'Invoice Number': 'Credit Memo Number', 'Amount': 'CM Value'})

        DF3 = pd.concat([invoiceDF, creditDF], axis=1)

        DF = pd.DataFrame()
        DF['ACCOUNT NUMBER'] = accountNumber
        DF['BILLING PERIOD'] = billingPeriod
        DF['INVOICE CURRENCY'] = invoiceCurrency
        DF['CREDIT MEMO CURRENCY'] = creditMemoCurrency

        mergedDF = pd.concat([DF, DF3], axis=1, ignore_index=True)

        # Last Load Date
        date = datetime.today().strftime('%Y-%m-%d')

        # Merging all seperated DF to single DF
        finalDF = mergedDF[mergedDF.columns[[0, 1, 5, 4, 2, 6, 8, 7, 3, 9]]]
        finalDF.columns = ['Account Number', 'Billing Period', 'Invoice Number', 'Invoice Description',
                           'Invoice Currency', 'Invoice Value', 'CM Number', 'CM Desc', 'CM Currency', 'CM Value']
        finalDF.reset_index(drop=True, inplace=True)

        # Database Dataframe
        dbDF = pd.DataFrame()
        dbDF['ACCOUNT_NUMBER'] = finalDF['Account Number']
        dbDF['BILLING_PERIOD'] = finalDF['Billing Period']
        dbDF['INVOICE_NUMBER'] = finalDF['Invoice Number']
        dbDF['INVOICE_DESCRIPTION'] = finalDF['Invoice Description']
        dbDF['INVOICE_CURRENCY'] = finalDF['Invoice Currency']
        dbDF['INVOICE_VALUE'] = finalDF['Invoice Value']
        dbDF['CM_NUMBER'] = finalDF['CM Number']
        dbDF['CM_DESCRIPTION'] = finalDF['CM Desc']
        dbDF['CM_CURRENCY'] = finalDF['CM Currency']
        dbDF['CM_VALUE'] = finalDF['CM Value']
        dbDF['PDF_FILE_NAME'] = inputFile
        dbDF['LAST_LOAD_DATE'] = date

        dbDF['INVOICE_VALUE'] = dbDF['INVOICE_VALUE'].str.replace(
            ",", "").astype(float)
        dbDF['CM_VALUE'] = dbDF['CM_VALUE'].str.replace(",", "").astype(float)

        # Resetting the index of Dataframe
        dbDF.reset_index(drop=True, inplace=True)

        # Database Connection
        user = os.getenv('USERNAME')
        passw = os.getenv('PASSWORD')
        host = os.getenv('HOST')
        port = 3306
        database = os.getenv('DATABASE')

        mydb = create_engine('mysql+mysqlconnector://' + user + ':' +
                             passw + '@' + host + ':' + str(port) + '/' + database, echo=False)
        mydb.connect()

        # Writing the Dataframe to Database
        dbDF.to_sql(name=os.getenv('TABLE'),
                    con=mydb, if_exists='append', index=False)

        # Return Final Dataframe
        return finalDF


# Uploading File
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # check if the post request has the files part
        if 'files[]' not in request.files:
            flash('No file attached')
            return redirect(request.url)
        files = request.files.getlist('files[]')
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            else:
                flash("NOTE : Only PDF files are Allowed. Please Select a Valid PDF!!")
                return redirect('/')
        return redirect('/download_file')
    return render_template('index.html')


# Downloading the Processed file
@app.route('/download_file', methods=["GET"])
def html_table():
    df = AWS_CM()
    for the_file in os.listdir(UPLOAD_FOLDER):
        file_path = os.path.join(UPLOAD_FOLDER, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(e)
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, sheet_name="Statements")
    writer.save()
    output.seek(0)
    return send_file(output, attachment_filename='Statements.xlsx', as_attachment=True)


# Calling the Application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
