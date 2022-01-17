import copy
import logging
import os
import json


def readfile(filepath):

    # Reads a .json file and returns a python dict.
    
    if not os.path.getsize(filepath) == 0:
        with open(filepath, "r") as file:
            jsondata = file.read()
        data = json.loads(jsondata)
    else: data = {}
    return data


def writefile(filepath, data):

    # Takes a python dict and writes it to a .json file.
    
    jsondata = json.dumps(data, indent=4, sort_keys=True)
    with open(filepath, "w") as file:
        file.write(jsondata)


def updatefile(directory):


    filepath = os.path.join(directory, "_data.json")
    imagedata = readfile(filepath)


    # Find files:
    filenames = []

    for file in os.listdir(directory):
        
        filename = os.fsdecode(file)

        if not filename[0] == "_":

            filenames.append(filename)


    # Add new files:
    newobj = {"date": "", "caption": "", "description": ""}
    for fn in filenames:

        if fn not in imagedata:

            imagedata[fn] = copy.deepcopy(newobj)

    # Clean missing files:
    dellist = []
    for image in imagedata:

        if image not in filenames:

            dellist.append(image)

    for i in dellist:
        del(imagedata[i])

    writefile(filepath, imagedata)


def getdatafiles(rootdir):
    
    directories = []

    for subdir, dirs, files in os.walk(rootdir):
        for file in files:
            if file == "_data.json":
                directories.append(subdir)

    return directories


def update(rootdir):
    directories = getdatafiles(rootdir)
    if len(directories) == 0:
        logging.info("No media files found.")
    else:
        for directory in directories:
            logging.info(f"Updating data for: {directory}.")
            updatefile(directory)
