# Padlet-Downloader
 
## requirements
  - pip install dsx
  - pip install wget

## instructions

1. clone the repo
2. place the downloaded excel file(s) into "padlet_excel_files" folder and organize into a sub-folder
3. run the "main.py" in "script" folder, the first required argument is the sub-folder's name

   ```python
   python main.py "Week_01" --download
   ```

4. optional argument -d --download is to download submission files and generate the additional filesize report. \
   The script will download all the files into "downloads", organized by in the sub-folder's name defined above.



