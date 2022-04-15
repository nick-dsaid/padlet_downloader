#!/usr/bin/env python
# coding: utf-8



import os
import sys
import re
import math
import wget
import requests
import logging
import tqdm
import argparse



from dsx.ds_utils import *



os.chdir(os.pardir)



logging.basicConfig(filename='padlet_extract.log',
                    filemode='w',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)

root = logging.getLogger()
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)




pat_email_group = '(([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-\-\.]+(\.[A-Z|a-z]{2,})+)'




# read emails and filter only to the emails
df_email_to_filter = pd.read_excel('data/participants_x.xlsx')
df_email_to_filter.email = df_email_to_filter.email.str.lower()


# Process the Downloaded Excel Files of the Week




parser = argparse.ArgumentParser()
parser.add_argument("filepath", help="folder_name for the week")
parser.add_argument("-d", "--download", action="store_true", help="download files and generate filesize report.")

args = parser.parse_args()
current_folder = args.filepath
download_bool = args.download

logging.info(f"current_file set as {current_folder}")
if download_bool:
    logging.info("Files will be downloaded to generate filesize report.\
    \nThis can take more than 5 minutes to run")





# # Simulate Argument
# # This line not needed when executed in block
# current_folder = 'Week_01'
# download_bool = True




# Reading in mapping file
df_mapp = pd.read_csv('data/DC Bootcamp - Service Accounts-623d1b9a0126670012303866.csv', skiprows=5)
df_mapp.ds.stdcols()

df_mapp.Official_Email = df_mapp.Official_Email.str.lower()
df_mapp.Official_Email = df_mapp.Official_Email.str.strip()
df_mapp['email'] = df_mapp.Official_Email.str.extract(pat_email_group)[0]
df_mapp.rename(columns={'Padlet_Username':'Author'}, inplace=True)

df_mapp.drop_duplicates(['email'], keep='last', inplace=True)



# Reading Padlet Files
dirpath = os.path.join('padlet_excel_files', current_folder)

dff = []
for filename in os.listdir(dirpath):
    excel_file = pd.ExcelFile(os.path.join(dirpath, filename))
    df_header = excel_file.parse(nrows=4)
    padlet_name = "_".join(df_header.columns[1].split())
    df = excel_file.parse(skiprows=5)
    df.ds.stdcols()
    
    part_string_pat = "Part "
    # Check if the week is using multiple "Parts"
    mask = (df.Subject.str.contains(part_string_pat)==True) & (df.Attachment.isnull()==True) & (df.Author.isnull()==True)
    if len(df[mask]) > 0:
        df['Part'] = None
        df.loc[mask, 'Part'] = df.Subject
        df.Part = df.Part.fillna(method='ffill')
        df = df[mask==False].copy()
        df = df.ds.cols_shift(['Part'], 0)
        
    df['padlet_name'] = padlet_name
    df = df.ds.cols_shift(['padlet_name'], 0)
    df['email'] = df.Subject.str.extract('(\[.+\])')
    df['email'] = df['email'].str[1:-1]
    dff.append(df)

df = pd.concat(dff, axis=0, ignore_index=True, sort=False)


## Merge Mapping File and Username




# There can be multiple "(" , use regex group for extration
pat = re.compile('((?<=\()[\d\w]+)')
# if bracket exits, then extract username between brackets
mask = (df.Author.str.find('(') != -1)
df.loc[mask, 'Author'] = df[mask].Author.map(lambda x: pat.findall(x)[-1])
# merging
df = df.drop('email', axis=1).merge(df_mapp[['Author', 'email']], 'left', 'Author')



# Getting Username not Registered in FormSG
# Export in the last stage
list_nonreg_authors = df[(df.email.isnull()) & (df.Author != 'Anonymous')].Author.unique()


## Safe Guard Summitter Profile

pat_email_group = '(([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-\-\.]+(\.[A-Z|a-z]{2,})+)'


# if Anonymous, try extract email from subject with regex
df.loc[df.email.isnull(), 'email'] = df[df.email.isnull()].Subject.str.extract(pat_email_group)[0]
df.loc[df.email.isnull(), 'email'] = df[df.email.isnull()].Body.str.extract(pat_email_group)[0]

df.email = df.email.str.lower()
df.email = df.email.str.strip()




# Convert Tz from UTC to +8
df.Updated_At = pd.to_datetime(df.Updated_At)
df.Created_At = pd.to_datetime(df.Created_At)

df.Updated_At = df.Updated_At.dt.tz_convert('Asia/Singapore')
df.Created_At = df.Updated_At.dt.tz_convert('Asia/Singapore')


# # Downloading the Task Files




# Filter before Downloading
dff = df[df.email.isin(df_email_to_filter.email)]


# This whole black only run if the "--download" argument is presence, which means "download_bool" is True




def create_folder_for_download(str: current_folder):
    export_path = os.path.join(os.getcwd(), 'downloads', current_folder)
    if os.path.exists(export_path) and os.path.isdir(export_path):
        logging.warning(f'Export path exists at {export_path}')
    else:
        os.mkdir(export_path)
        logging.info(f'Export path created at {export_path}')
    return export_path




def download_files_create_report(df_filtered) -> pd.core.frame.DataFrame:
    df_check_report = []

    for i, row in tqdm.tqdm(df_filtered.iterrows(), total=len(df_filtered)):
        if pd.isna(row.Attachment)==False:
            try:
                # Forming the filename for file to be downloaded
                filename_toset = os.path.basename(row.Attachment).split('.')
                filename_toset.insert(-1, "_" + row.email)
                filename_toset = ''.join(filename_toset[:-1]) + '.' + filename_toset[-1]

                path_file_download = os.path.join(export_path, filename_toset)
                wget.download(row.Attachment, path_file_download)
                file_size_kb = np.round(os.path.getsize(path_file_download) / 1024, 2)

                row['local_relative_path'] = path_file_download
                row['file_size_kb'] = file_size_kb
                df_check_report.append(row)
            except:
                logging.warning(f'File download failed for row.email')

    return pd.DataFrame(df_check_report)


# # checking report


if 'Part' in dff.columns:
    dff = dff.sort_values(['email', 'Part', 'Updated_At'], axis=0, ascending=True)
    dff = dff.drop_duplicates(['email', 'Part'], keep='last')

    df_report_submission = df_email_to_filter.merge(dff[['email', 'Part', 'Updated_At']], 'left', 'email')
    df_report_submission = df_report_submission.pivot_table(index='email', columns='Part', values='Updated_At', dropna=False)
    df_report_submission = df_report_submission.reset_index(drop=False)
else:

    dff = dff.sort_values(['email', 'Updated_At'], axis=0, ascending=True)
    dff = dff.drop_duplicates(['email'], keep='last')
    df_report_submission = dff[['email', 'Updated_At']].copy()
    df_report_submission = df_report_submission.reset_index(drop=True)

    
# Adding in Emails that have not submitted any files
missing = df_email_to_filter[~df_email_to_filter.email.isin(df_report_submission.email)]
df_temp = [{'email':x} for x in missing.email.tolist()]
df_report_submission = df_report_submission.append(df_temp)

df_report_submission = df_report_submission.merge(df_email_to_filter, 'left', 'email')
df_report_submission = df_report_submission.ds.cols_shift('agency', 'left')
df_report_submission = df_report_submission.sort_values(['agency', 'email'], axis=0)


# # Exporting Files


for g, dfg in df_report_submission.groupby('agency'):
    dfg.to_csv(os.path.join('reports', current_folder + f'_{g}_submission_report.csv'), index=False)
    
logging.info("Submission_report(s) have been exported")




if download_bool:
    logging.info("Starting to download files and generate fileszie report")
    export_path = create_folder_for_download(current_folder)
    df_report = download_files_create_report(dff)
    df_report = df_report.merge(df_email_to_filter, 'left', 'email')

    for g, dfg in df_report.groupby('agency'):
        dfg.to_csv(os.path.join('reports', current_folder + f'_{g}_filesize_report.csv'), index=False)




logging.info("Program executed completely. Terminated.")




# df_nonreg = pd.DataFrame(list_nonreg_authors).reset_index()
# df_nonreg.columns = ['No', 'Padlet_Username']
# df_nonreg.to_html('DCBootcamp_Padlet_Usernames.html', index=False)






