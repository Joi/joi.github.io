"""
Comment and Pseudo code outline of
Paprika JSON Export Package parser

Date: 2020-07-05
Author: Boris A.

References:
https://gist.github.com/mattdsteele/7386ec363badfdeaad05a418b9a1f30a
https://www.learnpython.org/
"""

# IMPORTS - Guessing here…
import os.path  # https://docs.python.org/3/library/os.path.html
import gzip     # https://docs.python.org/3/library/gzip.html
import json     # https://docs.python.org/3/library/json.html

# SET SCRIPT VARIABLES
paths['paprika_export'] = "/Users/joi/…/My Recipes.paprikarecipes"
paths['paprika_jekyll'] = "/path/to/…"

# Unzip the Paprika export archive

# This gives us a directory named "My Recipes"

# Get the list of files from inside "My Recipes"

# Start a loop to iterate over the files

# Prepare a cleaner filename we'll want for the Markdown Ouput (no spaces, etc)

# Open the file and un-gzip the string

# Decode the JSON into a Python data struct

# Prepare the Markdown string we want to write

# Creat teh output file with file name we prepared

# Dump the markdown string into it

# Close the loop

