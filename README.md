# Padlet-Downloader
 
## requirements
  - pip install dsx
  - pip install wget

## instructions
    1. clone the repo
    2. place the downloaded excel file into "padlet_excel_files"
    3. run the "main.py" script in "script" folder, the first required argument is the filename of the 
       "downloaded excel file", without the folder name.
  
       ```python
       python main.py "Padlet - Sample Padlet for Script Test.xlsx"
       ```
  
    4. the script will download all the files into "downloads", 
    organized by the Padlet's name (e.g. Week 01). 
    Each filename is appended with the email address of the submitter.
    5. the reports contain the csv file which have the details (including file size of the files).


