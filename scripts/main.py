#!/usr/bin/env python
# coding: utf-8



import os
import argparse
import wget
import requests
import logging
from dsx.ds_utils import *


os.chdir(os.pardir)


logging.basicConfig(filename='padlet_extract.log',
                    filemode='w',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.INFO)



# To-Do: read emails and filter only to the emails
email_list_to_filter = []

# To-Do: use Padlet-Email mapping file to cross-check emails and padlet username
# <here>


parser = argparse.ArgumentParser()
parser.add_argument("filepath", help="export excel filename from Padlet; omit directory")

args = parser.parse_args()
current_file = args.filepath
logging.info(f"current_file set as {current_file}")

excel_file = pd.ExcelFile(os.path.join('padlet_excel_files', current_file))


# To-Do: If header rows change, use search method
df_header = excel_file.parse(nrows=4)
padlet_name = "_".join(df_header.columns[1].split())
df = excel_file.parse(skiprows=5)
df.ds.stdcols()




part_string_pat = "Part "
if len(df[df.Subject.str.contains(part_string_pat)==True]) > 0:
    df['Part'] = None
    df.loc[df.Subject.str.contains(part_string_pat)==True, 'Part'] = df.Subject
    df.Part = df.Part.fillna(method='ffill')
    df = df[df.Subject.str.contains(part_string_pat)==False].copy()


df['padlet_name'] = padlet_name
df.ds.cols_shift(['padlet_name', 'Part'], 0)
df['email'] = df.Subject.str.extract('(\[.+\])')
df['email'] = df['email'].str[1:-1]



export_path = os.path.join(os.getcwd(), 'downloads', padlet_name)
if os.path.exists(export_path) and os.path.isdir(export_path):
    logging.warning(f'Export path exists at {export_path}')
else:
    os.mkdir(export_path)
    logging.info(f'Export path created at {export_path}')



df_check_report = []
for i, row in df.iterrows():
    if pd.isna(row.Attachment)==False:
        try:
            path_file_download = os.path.join(export_path, os.path.basename(row.Attachment) + "_" + row.email)
            wget.download(row.Attachment, path_file_download)
            file_size_kb = np.round(os.path.getsize(path_file_download) / 1024, 2)

            row['local_relative_path'] = path_file_download
            row['file_size_kb'] = file_size_kb
            df_check_report.append(row)
        except:
            logging.warning(f'File download failed for row.email')



df_check_report = pd.DataFrame(df_check_report)
df_check_report.to_csv(os.path.join('reports', '_'.join(current_file[:current_file.find('.')].split())) + '.csv')
logging.info(f"report exported  set as {'_'.join(current_file.split())}")




