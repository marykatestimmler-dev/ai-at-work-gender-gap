"""Download the March 2026 HTOPS public-use file from census.gov into data/raw/.
The Census Bureau has said it will repost this wave with corrected weights; re-run this script to pick up the corrected file."""
import os, urllib.request, zipfile
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'))
URL='https://www2.census.gov/programs-surveys/demo/datasets/hhp/2026/topical/HTOPS_HPS_2603_CSV.zip'
os.makedirs('data/raw',exist_ok=True); z='data/raw/HTOPS_HPS_2603_CSV.zip'
print('downloading',URL); urllib.request.urlretrieve(URL,z)
with zipfile.ZipFile(z) as f: f.extractall('data/raw')
print('extracted:',os.listdir('data/raw'))
