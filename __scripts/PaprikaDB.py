#!/usr/bin/env python3
# Paprika Database
# This script connects to Paprika app's SQLite database and pull out whatever we want and format it as JSON, YAML, whatever.

# NOTES:
# Before running the first time: 1. create a file in the same directory as this Notebook, named "config.py" 2. copy paste this line:
# path_project = "/local/path/to/this/repo/joi.github.io"
# (which should be the path to the direcotry one level up from where this file here is.)

# pip3 install mistletoe
# pip install Unidecode | https://pypi.org/project/Unidecode/
# pip install pathvalidate | https://pypi.org/project/pathvalidate/
# pip install pyyaml
# pip install python-frontmatter

# REGARDING MARKDOWN
# We ran with Commonmakr for a while but ran into an issue: it doesn't do tables.
# A quick fix was to switch to "Markdown-It" https://github.com/executablebooks/markdown-it-py


print("\n\n\n---------------------------------------\nEXECUTING PaprikaDB EXPORT\n---------------------------------------\n")

# IMPORTS -------------------------------------
# speedracergogogo
import time
start_time = time.time()

import os
import re
import shutil
import datetime
from datetime import datetime
import zipfile
import json
import yaml
from markdown_it import MarkdownIt
from mdit_py_plugins.footnote import footnote_plugin
#from mdit_py_plugins.front_matter import front_matter_plugin
import frontmatter
import pprint
from pathvalidate import sanitize_filename
import unidecode
import sqlite3
from sqlite3 import Error
from pathlib import Path
from shutil import copyfile
from collections import defaultdict
import config # This imports our local config file, "config.py". Access vars like so: config.var


# INITIALIZE CLASSES ------------------------------
# Markdown-It
mdit = (
    MarkdownIt()
    .use(footnote_plugin)
    #.use(front_matter_plugin)
    #.disable('image')
    .enable('table')
)

# VARS -----------------------------------------

# Debug?
debug = False

# Date time stamp
now = datetime.now()
# DT stamp restricted to the hour. For the local database backups.
dt_hourly = now.strftime("%Y-%m-%d %H.00")
#print(dt_hourly)

# Environment-dependent Paths
path_project    = config.path_project # manually set in config.py, which is NOT checked into GIT.
path_user_home  = str(Path.home())    # automatically detects the User home directory path from the OS/ENV

# Paprika Database Path
filename_db     = 'Paprika.sqlite'
path_paprika    = '/Library/Group Containers/72KVKW69K8.com.hindsightlabs.paprika.mac.v3/Data/'
path_db_sub     = path_paprika + 'Database/'
path_db_med     = path_user_home + path_db_sub
path_db_full    = path_user_home + path_db_sub + filename_db
path_photos     = path_user_home + path_paprika + 'Photos/'

# Paprika Databse Backup. / We create this before we do anything, just in case.
file_db_bu          = 'Paprika-BU-' + dt_hourly + '.sqlite'
path_db_bu_sub      = path_project + '/__scripts/backups/'
path_db_bu          = path_db_bu_sub + file_db_bu + '.zip'

# Replaces Above "Working"
path_temp_working   = path_db_bu_sub + "tmp/" # put tmp in backup
path_db_working     = path_temp_working + filename_db

# Output
path_output_json_data  = path_project + '/_data/'
path_output_recipe_mkdn_files = path_project + '/_recipes/'
path_output_meal_mkdn_files   = path_project + '/_notes/'
path_output_recipe_phot_files = path_project + '/images/recipes/'

# Paparika Timestamp Offset: 978307200
ts_offset = 978307200

print ("✅ IMPORTs completed and VARs initiated\n")

# - FUNCTIONS ----------------------------------

# Utility Functions ----------------------------

# Clobber a string into a filename -------------
def make_filename(string):
    string = unidecode.unidecode(string)
    # Need to strip out amperstands. See content.html liquid too.
    string = string.replace(" &","")
    string = string.replace(" ","-")
    #string = created[0:10] + "-" + string
    #string=str(bytes(string, 'utf-8').decode('utf-8','ignore').encode("utf-8",'ignore'))
    #string=string.replace("b'","").replace("'","")
    invalid = r'<>:"/\|?* ,()“”‘’\''
    for char in invalid:
        string = string.replace(char, '')
    string = sanitize_filename(string).lower().rstrip('-').replace('---','-')
    string = string.lower()
    
    return string

# Delete and Create Output Directories
def pheonix_output_directories(path):
  if os.path.exists(path):
    # if path exists, burn it down
    shutil.rmtree(path, ignore_errors=True)
  # and now raise it anew
  os.mkdir(path)

 # Turn a multiline text block into a Markdown List
def make_list(text):
    return "* " + text.replace("\n", "\n* ") 

# Database Functions ---------------------------

# Connect to Database
def db_connect(db_file):
    #conn = None
    try:
        conn = sqlite3.connect(db_file)
        # row_factory does some magic for us
        # see: https://stackoverflow.com/questions/3300464/how-can-i-get-dict-from-sqlite-query
        conn.row_factory = sqlite3.Row
    except Error as e:
        print(e)
    return conn


# Parse Paprika Markdown-ish into Markdown
    # if 0 == recipe -> pass 1 to make_filename()
    # if 0 == photo -> take 1 as key into {photos_dict} and get filename
def paprika_markdownish(content,photos_dict):
    if content:
        content = re.sub(r'\[(photo):(.+?)\]',lambda x: '![' + x.group(2) + '](/images/recipes/' + photos_dict[x.group(2)] + ')',content)
        #content = re.sub(r'\[(recipe):(.+?)\]',lambda x: '[' + x.group(2) + '](/recipes/' + make_filename(x.group(2)).lower() + ')',content)
        # This is for if we want ObsidianMD instead of regular
        content = re.sub(r'\[(recipe):(.+?)\]',lambda x: '[[' + make_filename(x.group(2)) + '|' + x.group(2) + ']]',content)
        return content
    else:
        raise ValueError("content null")

# Simple naïve wrapper around opening, writing to and closing a file.
def write_file(path,content):
    f = open(path, 'w')
    f.write(str(content))
    f.close()


print ("✅ FUNCTIONS defined\n")


# OUTPUT DESTINATION DIRECTORIES ---------------------

# If Output Paths don't exist, create them
if not os.path.exists(path_db_bu_sub):
    os.mkdir(path_db_bu_sub)

# These ones we want to recreate every time
# Recipe Markdown Stubs Directory
pheonix_output_directories(path_output_recipe_mkdn_files)
# Recipe Renamed Photos Directory
pheonix_output_directories(path_output_recipe_phot_files)

print ("✅ DIRECTORIES created\n")


# DATABASE BACKUPS -----------------------------------

# Make a zipped backup of the DB
zipfile.ZipFile(path_db_bu, mode='w').write(path_db_full, arcname=file_db_bu, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


# Make a temp copy of the DB to work with. We delete it later.
#
# First, check if the temp folder already exists and if so delete it
if os.path.exists(path_temp_working):
    shutil.rmtree(path_temp_working, ignore_errors=True) #nuke the temp working dir.

copy_DB_Return = shutil.copytree(path_db_med, path_temp_working) # create a var here just to capture the useless out put of the copyfile() function

print ("✅ DATABASE Backed up\n")



# DATABASE OPERATIONS ------------------------------

# First Database Operation: WAL Checkpoint
conn = db_connect(path_db_working)
cur = conn.cursor()
cur.execute("PRAGMA wal_checkpoint;")
conn.close()
# Second Database Operation: Get our recipe Data
conn = db_connect(path_db_working)
with conn:
    cur = conn.cursor()
    cur.execute(f"""
SELECT 
    GROUP_CONCAT(C.ZNAME,"|") as `categories`,
    R.ZCOOKTIME        as `cook_time`,
    R.ZINTRASH         as `intrash`,
    datetime(R.ZCREATED + {ts_offset},'unixepoch') as `created`,
    R.ZCREATED + {ts_offset}                       as `created_ts`,
    R.ZDESCRIPTIONTEXT as `description`,
    R.ZDIFFICULTY      as `difficulty`,
    R.ZDIRECTIONS      as `directions`,
    R.ZINGREDIENTS     as `ingredients`,
    R.ZIMAGEURL        as `image_url`,
    R.ZNAME            as `name`,
    R.ZNOTES           as `notes`,
    R.ZNUTRITIONALINFO as `nutritional_info`,
    R.ZPHOTO           as `photo_thumb`,
    R.ZPHOTOLARGE      as `photo_large`,
    R.ZPREPTIME        as `prep_time`,
    R.ZRATING          as `rating`,
    R.ZSERVINGS        as `servings`,
    R.ZSOURCE          as `source`,
    R.ZSOURCEURL       as `source_url`,
    R.ZTOTALTIME       as `total_time`,
    R.ZUID             as `uid`,
    R.Z_PK             as `p_recipe_id`,
    -- We need to do these SELECTS because
    -- otherwise the Category concat
    -- replicates itself the number of times
    -- there are images. No idea why.
    (
        SELECT
            GROUP_CONCAT(RP.ZFILENAME,"|") as filename
        FROM
            ZRECIPEPHOTO as RP
        WHERE
            RP.ZRECIPE = R.Z_PK
    ) as photos_filenames,
    (
        SELECT
            GROUP_CONCAT(RP.ZNAME,"|") as name
        FROM
            ZRECIPEPHOTO as RP
        WHERE
            RP.ZRECIPE = R.Z_PK
    ) as photos_names,
    (
        SELECT
            GROUP_CONCAT(date(M.ZDATE + {ts_offset},'unixepoch'),"|") as dates
        FROM
            ZMEAL AS M
        WHERE
            M.ZRECIPE = R.Z_PK
    ) as meal_dates,
    (
        SELECT
            GROUP_CONCAT(M.ZTYPE,"|") as types
        FROM
            ZMEAL AS M
        WHERE
            M.ZRECIPE = R.Z_PK
    ) as meal_types

FROM
    ZRECIPE as R

LEFT JOIN    Z_12CATEGORIES AS RC
    ON    RC.Z_12RECIPES = R.Z_PK
LEFT JOIN    ZRECIPECATEGORY AS C
    ON    RC.Z_13CATEGORIES = C.Z_PK

WHERE
  R.ZINTRASH IS 0

GROUP BY    R.Z_PK;
"""
    )
#  AND ( R.ZRATING = 5 OR C.ZNAME LIKE '%mine%')
    
# --------------------------------------------------------------------------------------
# For the next bit with columns and results and dict and zip, see:
#    https://stackoverflow.com/questions/16519385/output-pyodbc-cursor-results-as-python-dictionary/16523148#16523148
#

# This grabs the key (cur.description) for us
columns = [column[0] for column in cur.description]
rows = cur.fetchall()

results = []
for row in rows:
    # and here we glue the key to the value
    results.append(dict(zip(columns, row)))

print ("✅ DATABASE Queried For Recipes\n")



# --------------------------------------------------------------------------------------
# Create a dict to hold the cats -> recipes dictionary
cats = {}
photos = defaultdict(dict)
# --------------------------------------------------------------------------------------
# Loop through Results
for result in results:
    result['photos_dict'] = {}
    result['html'] = {}
    result['type'] = None
    result['mine'] = None

    # RECIPE_FILENAME : 
    # This is also our Key between the YAML in Markdown stubs and the JSON Data files
    recipe_filename = make_filename(result['name'])
    result['slug'] = recipe_filename
    result['permalink'] = '/recipes/'+recipe_filename



    # --------------------------------------------------------------------------------------
    # Start of RESULT Items FOR loop {



    # ---------------------------------------------------
    # Photos Stuff
    # We do this first so we have access to the photo data when parsing Paprika Markdown-ish [photo:name]
    # Split concatened photo filenames and names into a lists
    try:
        result['photos_filenames'] = result['photos_filenames'].split('|')
    except:
        pass
    try:
        result['photos_names'] = result['photos_names'].split('|')
        # if we have photo_names, zip filenames & names into into a key=value dict
        # We will use this for the PMD parse below
        result['photos_dict'] = dict(zip(result['photos_names'], result['photos_filenames']))
    except:
        result['photos_dict'] = None
        pass

    # ----------------------------------------------------------------
    # Some notes about photos ----------------------------------------
    # Paprika has several types of photos it manages in different ways:
    # 1. The Recipe Thumbnail
    #     a) This is either generated from the source recipe, 
    #        or set from the first photo uploaded to the recipe
    #     b) its UID is stored in the Recipe table, in the PHOTO column.
    # 2. The Recipe "large photo"
    #     a) Same provenance as Thumbnail, just the larger version of it.
    # 3. User-uploaded photos
    #     a) photos the user uploads into Paprika themselves are assigned UIDs 
    #        and numbered names (editable in the recipe edit view).
    #     b) all their metadata is stored in its own table ('ZRECIPEPHOTO') 
    #        and related via the recipe ID (not UID)
    #
    #  We need to copy both kinds with new file names over. 
    #  The thumbs will simply be named "thumb"
    #
    # ----------------------------------------------------------------

    # Disabled. I generated this and printed out a JSON file to use as a guide. Not needed in production, 
    # but as we ain't done yet, keeping it around.
    #photos[result['uid']] = {'recipe_filename':recipe_filename,'recipe_thumb':result['photo_thumb'], 'recipe_photos':result['photos_dict']}

    # We need to move and rename the photo files and vars (which go into the recipe stubs), here, all at once. 
    result['photos_filenames_new'] = []
    result['photos_dict_new'] = {}

    # First, if this recipe result has any photos
    if result['photo_thumb'] or result['photos_dict']:
      source_path_recipe_photos = path_photos + result['uid'] + "/"
      dest_path_recipe_photos = path_output_recipe_phot_files + "/"

      if result['photo_thumb']:
        try:
          # New photo_thumb file name
          new_photo_thumb = recipe_filename + "-thumb.jpg"
          #copy the thumbnail over
          shutil.copy2(source_path_recipe_photos + "/" + result['photo_thumb'], dest_path_recipe_photos + new_photo_thumb)
          result['photo_thumb'] = new_photo_thumb
          if debug:
            print("\t- Thumb: " + recipe_filename + "")
        except:
          print( "🛑 THUMBNAIL PHOTO Missing for " + recipe_filename )

      if result['photo_large']:
        try:
          # New photo_large file name
          new_photo_large = recipe_filename + "-large.jpg"
          #copy the large photo over
          shutil.copy2(source_path_recipe_photos + "/" + result['photo_large'], dest_path_recipe_photos + new_photo_large)
          result['photo_large'] = new_photo_large
          if debug:
            print("\t- Large: " + recipe_filename + "")
        except:
          print( "🛑 LARGE PHOTO Missing for " + recipe_filename )

      if result['photos_dict']:
        #print("\n" + recipe_filename + ": has photos_dict")
        for photo_name,pd2 in result['photos_dict'].items():
          photo_name_fn = make_filename(photo_name)
          #print("\tphoto name:" + photo_name + "\n\tphoto UID:" + pd2)
          try:
            new_photo_filename = recipe_filename + "-" + photo_name_fn + ".jpg"
            shutil.copy2(source_path_recipe_photos + "/" + pd2,dest_path_recipe_photos + new_photo_filename)
            result['photos_filenames_new'].append(new_photo_filename)
            result['photos_dict_new'][photo_name] = new_photo_filename
            if debug:
              print("\t- Moved: " + new_photo_filename + "")

          except Exception as e:
            print( "🛑 MISSING PHOTOS for " + recipe_filename + ": " + new_photo_filename )
            #print(e)
            print("-------")
        
        result['photos_dict'] = result['photos_dict_new']



    # ---------------------------------------------------
    # Meal Dates
    # Split concatened mealdates into a list
    rmeal_dates = ""
    if result['meal_dates']:
      try:
        result['meal_dates'] = result['meal_dates'].split('|')
        for meal_date in result['meal_dates']:
          rmeal_dates += "- [[" + meal_date + "|recipenote]]\n"
        rmeal_dates  = mdit.render(rmeal_dates)
        #if debug:
            #print("\t- MD'ed Meal Dates: " + rmeal_dates + "")
        
      except Exception as e:
          print( "🛑 Something fubar in rmeal_dates: " + rmeal_dates + "\n")
          print(e)
          print("-------\n")



    # ---------------------------------------------------
    # Directions, Descriptions, Ingredients, Nutritional Info
    if result['directions']:
      rdirections  = paprika_markdownish(result['directions'],result['photos_dict'])
      rdirections  = mdit.render(rdirections)
    else:
      rdirections = None

    if result['description']:
      rdescription = paprika_markdownish(result['description'],result['photos_dict'])
      rdescription = mdit.render(rdescription)
    else:
      rdescription = None

    if result['ingredients']:
      list_ing_lines   = paprika_markdownish(result['ingredients'],result['photos_dict'])
      list_ing_lines   = re.sub('\\\\x{0D}','\n',list_ing_lines)
      list_ing_lines   = re.sub('\n\n','\n',list_ing_lines)
      list_ing_lines   = make_list(list_ing_lines)
      ringredients = mdit.render(list_ing_lines)
    else:
      ringredients = None

    if result['nutritional_info']:
      rnutrition = mdit.render(str(result['nutritional_info']))
    else:
      rnutrition = None

    if result['notes']:
      result['notes'] = paprika_markdownish(result['notes'],result['photos_dict'])
      rnotes = mdit.render(result['notes'])
    else:
      rnotes = None

    result['html'] = {
      'directions'  : rdirections,
      'description' : rdescription,
      'ingredients' : ringredients,
      'nutrition'   : rnutrition,
      'notes'       : rnotes,
      'meal_dates' : rmeal_dates
      }

    # ---------------------------------------------------
    # Categories
    # Split concatened categories into a list
    if result['categories']:
        try:
            result['categories'] = result['categories'].split('|')
            for cl in result['categories']:
              
              # Using the categories as a toggle hack ("recipe by Joi or not", etc…)
              if cl == "_mine":
                result['mine'] = 1
              if cl == "_stub":
                result['type'] = 'stub'

              if cl not in cats.keys():
                cats[cl] = {}

              if recipe_filename not in cats[cl].keys():
                cats[cl][recipe_filename] = str(result['name'])

        except Exception as e:
          print( "🛑 Something fubar in categories for " + recipe_filename + "\n")
          print(e)
          print("-------\n")
        remove_cats_hacks = ['_mine','_stub']
        result['categories'] = [i for i in result['categories'] if i not in remove_cats_hacks]
        result['tags'] = result['categories']

    # ---------------------------------------------------
    # Sources
    if result["source"] == "":
        result["source"] = None 
    if result["source_url"] == "":
        result["source_url"] = None 

    # Clean out a bit of stuff
    result.pop('photos_dict_new')
    result.pop('photos_filenames')
    result.pop('photos_filenames_new')
    result.pop('photos_names')

    # end of RESULT Items FOR loop }
    # --------------------------------------------------------------------------------------

    
    # Going to split the "result" array into bits we want in the YAML and stuff we will put
    # in the content body
    result2 = result
    content = {}
    content["html"] = result2['html']
    del result2['html'], result2['directions'], result2['notes'], result2['nutritional_info']
    # We keep "result2['ingredients']" because content.html needs it for link previews.

    output2  = "---\n"
    output2 += "title: \"" + result2['name'] + "\"\n"
    output2 += "filename: \"" + recipe_filename + "\"\n"
    # Dumping all recipe metadata as YAML here
    output2 += yaml.dump(result2)
    output2 += "---\n"

    # We open Row One and include  _includes/backlinks.html in the _layouts/recipe.html tempplate.
    output2 += '<div class="large-8 medium-7 columns" id="writeup">'
    if result2['mine']:
      if content['html']['description']:
        output2 += '\t\t<div id="description"><h4>Description</h4>\n<div class="box box-description content">'+ content['html']['description'] + '</div></div>'
      if content['html']['notes']:
        output2 += '\t\t<div id="notes"><h4>Notes</h4>\n<div class="box box-notes">' + content['html']['notes'] + '</div></div>'
    output2 += '\t</div><!-- #writeup -->\n'
    output2 += '</div><!-- #row-one -->\n'

    output2 += '<div class="row" id="row-two">'
    output2 += '\t<div class="medium-4 small-5 columns" id="ingredients">'
    if content['html']['ingredients']:
        output2 += '<h4>Ingredients</h4><div class="box box-ingredients content">' + content['html']['ingredients'] + '</div>'
    output2 += '\t</div>'
    output2 += '\t<div class="medium-6 small-7 columns" id="directions">'
    if result2['mine']:
      if content['html']['directions']:
        output2 += '<h4>Directions</h4><div class="box box-directions content">' + content['html']['directions'] + '</div>'
    output2 += '\t</div>'


    # Create/Open a text file for each recipe and write the above Markdown string into it
    mdFilePath = path_output_recipe_mkdn_files + recipe_filename + ".md"
    write_file(mdFilePath,output2)

    del result,result2,output2,content

print ("✅ RECIPE RESULTS Looped and Acted upon\n")
# END RECIPES ---------------------------------------------------------------------




# START MEALS ---------------------------------------------------------------------

# Second Database Operation: Get our recipe Data
conn = db_connect(path_db_working)
with conn:
    cur = conn.cursor()
    cur.execute(f"""
SELECT 
    M.ZRECIPE as recipe_id,
    M.ZNAME as recipe_name,
    M.ZDATE + {ts_offset}                       as `meal_date_ts`,
    DATE(M.ZDATE, 'unixepoch', '+31 year', 'localtime') as `meal_date`,
    M.ZTYPE as meal_type_code,
    MT.ZNAME as meal_type_name

FROM
    ZMEAL as M

LEFT JOIN    ZMEALTYPE AS MT
    ON    MT.Z_PK = M.ZTYPE

WHERE
  M.ZRECIPE is not NULL

GROUP BY    M.Z_PK
ORDER BY
    meal_date_ts ASC
;
"""
    )

    
# --------------------------------------------------------------------------------------
# For the next bit with columns and results and dict and zip, see:
#    https://stackoverflow.com/questions/16519385/output-pyodbc-cursor-results-as-python-dictionary/16523148#16523148
#

# This grabs the key (cur.description) for us
columns = [column[0] for column in cur.description]
rows = cur.fetchall()

data_meals = []
for row in rows:
    # and here we glue the key to the value
    data_meals.append(dict(zip(columns, row)))

print ("✅ DATABASE Queried For Meals\n")

# Initialise MEALS Indices dict
meals_indices = defaultdict(dict)
# RECIPE by DATE and MEAL
meals_indices['recipe_by_date_and_meal'] = defaultdict(dict)
# MEAL by RECIPE and DATE
meals_indices['meal_by_recipe_and_date'] = defaultdict(dict)
# MEAL GROUPED NOTES & DATA by RECIPE and DATE
meals_indices['meal_data_by_recipe_and_status'] = defaultdict(dict)
# MEAL by DATE and RECIPE
meals_indices['meal_by_date_and_recipe'] = defaultdict(dict)

# Loop the data into the new struct
for data_meal in data_meals:
  meal_date             = data_meal['meal_date']
  meal_recipe_id        = data_meal['recipe_id']
  meal_recipe_name      = data_meal['recipe_name']
  meal_recipe_filename  = make_filename(data_meal['recipe_name'])
  meal_type_name        = data_meal['meal_type_name']



  # RECIPE by DATE and MEAL ---
  # If the `meal_type_name` key doesn't exist, we need to initialise the list
  try:
    meals_indices['recipe_by_date_and_meal'][meal_date][meal_type_name]
  except:
    meals_indices['recipe_by_date_and_meal'][meal_date][meal_type_name] = []
  
  # Creating both here and can decide later which one to use.
  # Create the meal dict with name and filename
  append_meal_dict = {
    'recipe_id'       : meal_recipe_id,
    'recipe_filename' : meal_recipe_filename,
    'recipe_name'     : meal_recipe_name
  }
  # Create the meal id list (we'll need to do lookup in recipe YAML data)
  append_meal_list = meal_recipe_id



  # and append it to the existing date dict, which is "defaultdicts" initialised before the FOR
  meals_indices['recipe_by_date_and_meal'][meal_date][meal_type_name].append(append_meal_list)

  # MEAL by RECIPE and DATE ---
  meals_indices['meal_by_recipe_and_date'][meal_recipe_id][meal_date] = meal_type_name

  # MEAL by DATE and RECIPE ---
  meals_indices['meal_by_date_and_recipe'][meal_date][meal_recipe_id] = meal_type_name



  # MEAL GROUPED NOTES & DATA by RECIPE and DATE ---

  note_file = path_output_meal_mkdn_files + meal_date + "-" + meal_type_name + ".md"
  append_nofile_regular = {'date': meal_date, 'type': meal_type_name}

  if os.path.isfile(note_file):
    parsed_note = frontmatter.load(note_file)
    try:
      append_featured = {'date': meal_date, 'type': meal_type_name, 'feature': parsed_note['feature']}
      #print("featured: " + str(meal_recipe_id).zfill(3) + " : " + json.dumps(append_featured))
      try:
        meals_indices['meal_data_by_recipe_and_status'][meal_recipe_id]['featured']
      except:
        meals_indices['meal_data_by_recipe_and_status'][meal_recipe_id]['featured'] = []
      meals_indices['meal_data_by_recipe_and_status'][meal_recipe_id]['featured'].append(append_featured)
    except:
      #append_regular = {'date': meal_date, 'type': meal_type_name}
      #print("regular : " + str(meal_recipe_id).zfill(3) + " : " + json.dumps(append_regular))
      try:
        meals_indices['meal_data_by_recipe_and_status'][meal_recipe_id]['regular']
      except:
        meals_indices['meal_data_by_recipe_and_status'][meal_recipe_id]['regular'] = []
      meals_indices['meal_data_by_recipe_and_status'][meal_recipe_id]['regular'].append(append_nofile_regular)
  else:
    #append_nofile = {'date': meal_date, 'type': meal_type_name}
    #print("nofile  : " + str(meal_recipe_id).zfill(3) + " : " + json.dumps(append_nofile))
    try:
      meals_indices['meal_data_by_recipe_and_status'][meal_recipe_id]['nofile']
    except:
      meals_indices['meal_data_by_recipe_and_status'][meal_recipe_id]['nofile'] = []
    meals_indices['meal_data_by_recipe_and_status'][meal_recipe_id]['nofile'].append(append_nofile_regular)



print ("✅ MEAL RESULTS Looped and Acted upon\n")

# CLOSE DB ------------------------------------------------------------------------
conn.close()

print ("✅ DATABASE Closed\n")






# File writing and Miscellaneous cleanup ------------------------------------------

# Convert the data structs to JSON and dump to individual files

# Category Indices
json_cats_dump = json.dumps(cats, ensure_ascii=False, sort_keys=True, indent=1)
jsonDataPath = path_output_json_data + "recipe_categories.json"
write_file(jsonDataPath,json_cats_dump)
print ("✅ CATEGORY JSON Indices Dumped\n")

# Meals Indices
json_meals_indices_dump = json.dumps(meals_indices, ensure_ascii=False, sort_keys=True, indent=1)
json_meals_indices_path = path_output_json_data + "meals_indices.json"
write_file(json_meals_indices_path,json_meals_indices_path)
print ("✅ MEALS JSON Indices Dumped\n")





# CLEANUP --------------------------------------------
# Delete the temp working direcotry
shutil.rmtree(path_temp_working, ignore_errors=True) # "ignore errors" nukes it
print ("\n✅ CLEANUP Complete\n")

exectime = round((time.time() - start_time),3)
print("------------------------------\n⏱  %s seconds \n------------------------------\n" % exectime)
print ("😎🤙🏼 We're done here.\n")