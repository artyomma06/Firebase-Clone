# More details at: 
#     https://flask.palletsprojects.com/en/2.2.x/

from flask import Flask, jsonify, request
import pymongo
from pymongo.server_api import ServerApi
import pprint
import json
import uuid
from functools import cmp_to_key

# Need to add your own client below
client = pymongo.MongoClient("add your client here", server_api=ServerApi('1'))
db = client.test
collection = db.fire

# Function to compare two keys (for sorting purposes)
def key_cmp(a, b):
    # Copy the keys to avoid modifying the original input
    ah = a
    bh = b

    # If the key starts with '-', remove it for comparison
    if a[0] == '-':
        ah = a[1:]
    if b[0] == '-':
        bh = b[1:]

    # Compare the modified keys
    if ah > bh:
        return 1
    elif ah == bh:
        return 0
    else:
        return -1

# Create a key function for sorting based on the key_cmp function
key_items_cmp = cmp_to_key(key_cmp)

# Function to compare two items based on their third element
def third_cmp(a, b):
    # Extract the third elements of the items for comparison
    ah = a[1]
    bh = b[1]

    # Compare the third elements
    if ah > bh:
        return 1
    elif ah == bh:
        return 0
    else:
        return -1

# Create a key function for sorting based on the third_cmp function
third_items_cmp = cmp_to_key(third_cmp)

app = Flask(__name__)

@app.route('/', defaults={'myPath': ''}, )
@app.route('/<path:myPath>', methods=['PUT'])
# Function to handle requests and update a MongoDB collection
def catch_all_put(myPath):
    # Create a response dictionary with information from the request
    resp = {
        "database": request.url_root,
        "path": request.path,
        "full path": request.full_path,
        "data": request.get_data().decode('utf-8')
    }

    # Check if the requested URI ends with ".json?"
    if resp["full path"][-6:] != ".json?":
        return "append .json to your request URI to use the REST API."

    # Connect to the MongoDB collection named 'posts'
    posts = db.posts

    # Handle different cases based on the request URI
    if resp["full path"] == "/.json?":
        # Clear the entire 'posts' collection
        posts.delete_many({})

        # Parse and insert the incoming JSON data into the collection
        data = json.loads(resp["data"])
        if isinstance(data, dict):
            keys = list(data.keys())
            temp = []
            for i in keys:
                temp.append({i: data[i]})
            post_id = posts.insert_many(temp)
        elif isinstance(data, list):
            group = [{str(i): x} for i, x in enumerate(data)]
            post_id = posts.insert_many(group)
        else:
            post = {"Ankapt": data}
            post_id = posts.insert_one(post).inserted_id
    else:
        # Clear specific entry in the 'posts' collection
        posts.delete_one({"Ankapt": {"$exists": True}})

        # Parse the request URI and update the corresponding data in the collection
        x = resp["full path"].split("/")
        x = x[1:]
        path = []
        for i in range(len(x) - 1):
            path.append(x[i])

        lastofus = x[-1].split('.')
        if len(lastofus[0]) != 0:
            path.append(lastofus[0])

        currentdata = json.loads(resp["data"])
        currentpath = '.'.join(path)
        startingpoint = path[0]

        count = 10
        if isinstance(currentdata, list):
            temp = {}
            for i in range(len(currentdata)):
                temp[str(i)] = currentdata[i]
            currentdata = temp

        try:
            # Attempt to update the existing entry in the 'posts' collection
            count = posts.update_one({startingpoint: {"$exists": True}}, {"$set": {currentpath: currentdata}}).matched_count
        except:
            # Handle the case when the update fails by unsetting parts of the path
            for i in range(len(path)):
                secondcurrentpath = '.'.join(path[0:len(path) - i])
                secondcount = posts.update_one({secondcurrentpath: {"$exists": True}}, {"$unset": {secondcurrentpath: ""}}).matched_count
                if secondcount == 1:
                    break
            # Retry the update after unsetting parts of the path
            count = posts.update_one({startingpoint: {"$exists": True}}, {"$set": {currentpath: currentdata}}).matched_count

        # If the entry does not exist, create a new entry in the 'posts' collection
        if count == 0:
            for i in range(len(path)):
                currentdata = {path[len(path) - 1 - i]: currentdata}
            post = {startingpoint: currentdata[startingpoint]}
            post_id = posts.insert_one(post).inserted_id

    # Return the data from the request
    return resp["data"]

@app.route('/', defaults={'myPath': ''})
@app.route('/<path:myPath>', methods=['DELETE'])
# Function to handle DELETE requests and update a MongoDB collection
def catch_all_Delete(myPath):
    # Create a response dictionary with information from the request
    resp = {
        "database": request.url_root,
        "path": request.path,
        "full path": request.full_path
    }

    # Check if the requested URI ends with ".json?"
    if resp["full path"][-6:] != ".json?":
        return "append .json to your request URI to use the REST API."

    # Connect to the MongoDB collection named 'posts'
    posts = db.posts

    # Handle different cases based on the request URI
    if resp["full path"] == "/.json?":
        # Clear the entire 'posts' collection
        posts.delete_many({})
    else:
        # Parse the request URI and update the corresponding data in the collection
        x = resp["full path"].split("/")
        x = x[1:]
        path = []
        for i in range(len(x) - 1):
            path.append(x[i])

        lastofus = x[-1].split('.')
        if len(lastofus[0]) != 0:
            path.append(lastofus[0])
        currentpath = '.'.join(path)

        # Handle deletion based on the structure of the URI path
        if len(path) == 1:
            # Delete the entire entry with the specified key
            count = posts.delete_one({path[0]: {"$exists": True}}).deleted_count
        else:
            # Update the entry to unset the specified path
            existed = posts.update_one({currentpath: {"$exists": True}}, {"$unset": {currentpath: ""}}).matched_count

            if existed == 1:
                # Handle deletion of intermediate paths with empty values
                for i in reversed(range(len(path[1:-1]))):
                    minipath = '.'.join(path[:(i + 2)])
                    status = posts.update_one({minipath: {"$exists": True, "$eq": {}}}, {"$unset": {minipath: ""}}).matched_count

                # Delete the top-level entry if it's empty after the update
                lastcount = posts.delete_one({path[0]: {"$exists": True, "$eq": {}}}).deleted_count

    # Return "null" as the response
    return "null"

@app.route('/<path:myPath>', methods=['POST'])
# Function to handle POST requests and update a MongoDB collection
def catch_all_post(myPath):
    # Create a response dictionary with information from the request
    resp = {
        "database": request.url_root,
        "path": request.path,
        "full path": request.full_path,
        "data": request.get_data().decode('utf-8')
    }

    # Check if the requested URI ends with ".json?"
    if resp["full path"][-6:] != ".json?":
        return "append .json to your request URI to use the REST API."

    # Connect to the MongoDB collection named 'posts'
    posts = db.posts

    # Generate a unique ID for the new data entry
    id = '-' + str(uuid.uuid4()).replace("-", "")[:19]

    # Handle different cases based on the request URI
    if resp["full path"] == "/.json?":
        # Parse and insert the incoming JSON data into the collection
        data = json.loads(resp["data"])
        if isinstance(data, list):
            data = [{str(i): x} for i, x in enumerate(data)]
        insert = {id: data}
        post_id = posts.insert_one(insert).inserted_id
    else:
        # Parse the request URI and update the corresponding data in the collection
        x = resp["full path"].split("/")
        x = x[1:]
        path = []
        for i in range(len(x) - 1):
            path.append(x[i])

        lastofus = x[-1].split('.')
        if len(lastofus[0]) != 0:
            path.append(lastofus[0])

        path.append(id)
        currentdata = json.loads(resp["data"])
        currentpath = '.'.join(path)
        startingpoint = path[0]

        count = 10
        if isinstance(currentdata, list):
            temp = {}
            for i in range(len(currentdata)):
                temp[str(i)] = currentdata[i]
            currentdata = temp

        try:
            # Attempt to update the existing entry in the 'posts' collection
            count = posts.update_one({startingpoint: {"$exists": True}}, {"$set": {currentpath: currentdata}}).matched_count
        except:
            # Handle the case when the update fails by unsetting parts of the path
            for i in range(len(path)):
                secondcurrentpath = '.'.join(path[0:len(path) - i])
                secondcount = posts.update_one({secondcurrentpath: {"$exists": True}}, {"$unset": {secondcurrentpath: ""}}).matched_count
                if secondcount == 1:
                    break
            # Retry the update after unsetting parts of the path
            count = posts.update_one({startingpoint: {"$exists": True}}, {"$set": {currentpath: currentdata}}).matched_count

        # If the entry does not exist, create a new entry in the 'posts' collection
        if count == 0:
            for i in range(len(path)):
                currentdata = {path[len(path) - 1 - i]: currentdata}
            post = {startingpoint: currentdata[startingpoint]}
            post_id = posts.insert_one(post).inserted_id

    # Return a JSON response with the generated ID
    return '{name:"' + id + '"}'

@app.route('/', defaults={'myPath': ''})
@app.route('/<path:myPath>', methods=['PATCH'])
# Function to handle PATCH requests and update a MongoDB collection
def catch_all_patch(myPath):
    # Create a response dictionary with information from the request
    resp = {
        "database": request.url_root,
        "path": request.path,
        "full path": request.full_path,
        "data": request.get_data().decode('utf-8')
    }

    # Connect to the MongoDB collection named 'posts'
    posts = db.posts

    # Check if the requested URI ends with ".json?"
    if resp["full path"][-6:] != ".json?":
        return "append .json to your request URI to use the REST API."

    # Parse the incoming JSON data
    data = json.loads(resp["data"])

    # Check if the parsed data is a dictionary
    if not isinstance(data, dict):
        return {"error": "Invalid data; couldn't parse JSON object. Are you sending a JSON object with valid key names?"}

    # Handle different cases based on the request URI
    if resp["full path"] == "/.json?":
        # Update or insert entries based on the keys in the incoming data
        keys = list(data.keys())
        temp = []
        for i in keys:
            try:
                # Attempt to delete the existing entry with the key
                count = posts.delete_one({i: {"$exists": True}}).deleted_count
                temp.append({i: data[i]})
            except:
                # If deletion fails, append the data without deleting
                temp.append({i: data[i]})
        # Insert the modified or new data entries into the collection
        post_id = posts.insert_many(temp)
    else:
        # Parse the request URI to determine the update path
        x = resp["full path"].split("/")
        x = x[1:]
        path = []
        for i in range(len(x) - 1):
            path.append(x[i])

        lastofus = x[-1].split('.')
        if len(lastofus[0]) != 0:
            path.append(lastofus[0])
        currentpath = '.'.join(path)
        startingpoint = path[0]

        # Find the existing data at the specified path
        whatsthere = posts.find_one({currentpath: {"$exists": True}})
        if whatsthere is not None:
            for i in path:
                whatsthere = whatsthere[i]
            # Update the existing data with the new data
            for i in data.keys():
                whatsthere[i] = data[i]
            data = whatsthere

        currentdata = data
        count = 10
        try:
            # Attempt to update the existing entry in the 'posts' collection
            count = posts.update_one({startingpoint: {"$exists": True}}, {"$set": {currentpath: currentdata}}).matched_count
        except:
            # Handle the case when the update fails by unsetting parts of the path
            for i in range(len(path)):
                secondcurrentpath = '.'.join(path[0:len(path) - i])
                secondcount = posts.update_one({secondcurrentpath: {"$exists": True}}, {"$unset": {secondcurrentpath: ""}}).matched_count
                if secondcount == 1:
                    break
            # Retry the update after unsetting parts of the path
            count = posts.update_one({startingpoint: {"$exists": True}}, {"$set": {currentpath: currentdata}}).matched_count

        # If the entry does not exist, create a new entry in the 'posts' collection
        if count == 0:
            for i in range(len(path)):
                currentdata = {path[len(path) - 1 - i]: currentdata}
            post = {startingpoint: currentdata[startingpoint]}
            post_id = posts.insert_one(post).inserted_id

    # Return the data from the request
    return resp["data"]

@app.route('/', defaults={'myPath': ''})
@app.route('/<path:myPath>', methods=['GET'])
# Function to handle GET requests and query a MongoDB collection
def catch_all_get(myPath):
    # Create a response dictionary with information from the request
    resp = {
        "database": request.url_root,
        "path": request.path,
        "full path": request.full_path
    }

    # Extract query parameters from the request
    orderby = request.args.get('orderBy')
    limittofirst = request.args.get('limitToFirst')
    limittolast = request.args.get('limitToLast')
    startat = request.args.get('startAt')
    endat = request.args.get('endAt')
    equalto = request.args.get('equalTo')

    # Validate query parameters
    if orderby is None and (limittolast is not None or limittofirst is not None or startat is not None or endat is not None or equalto):
        return {"error": "orderBy must be defined when other query parameters are defined"}

    # Attempt to convert limit parameters to integers or handle invalid values
    try:
        limittolast = int(limittolast) if limittolast is not None else limittolast
    except:
        limittolast = limittolast

    try:
        limittofirst = int(limittofirst) if limittofirst is not None else limittofirst
    except:
        limittofirst = limittofirst

    # Validate limit parameters
    if isinstance(limittofirst, str):
        if len(limittofirst) == 0:
            return {"error": "limitToFirst must be positive"}
        return {"error": "limitToFirst must be an integer"}

    if isinstance(limittolast, str):
        if len(limittolast) == 0:
            return {"error": "limitToLast must be positive"}
        return {"error": "limitToLast must be an integer"}

    if limittolast is not None:
        if limittofirst is not None:
            return {"error": "Only one of limitToFirst and limitToLast may be specified"}
        if limittolast <= 0:
            return {"error": "limitToLast must be positive"}

    if limittofirst is not None:
        if limittofirst <= 0:
            return {"error": "limitToLast must be positive"}

    if equalto is not None and (startat is not None or endat is not None):
        return {"error": "equalTo cannot be specified in addition to startAfter, startAt, endAt, or endBefore"}

    if equalto is not None:
        if orderby == '"$key"' and (equalto[0] != '"' or equalto[-1] != '"'):
            return {"error": "Provided key index type is invalid, must be string"}

    if startat is not None:
        if orderby == '"$key"' and (startat[0] != '"' or startat[-1] != '"'):
            return {"error": "Provided key index type is invalid, must be string"}

    if endat is not None:
        if orderby == '"$key"' and (endat[0] != '"' or endat[-1] != '"'):
            return {"error": "Provided key index type is invalid, must be string"}

    # Connect to the MongoDB collection named 'posts'
    posts = db.posts

    # Check if the requested path ends with ".json"
    if resp["path"][-5:] != ".json":
        return ''

    # Initialize results dictionary
    results = {}

    if resp["path"] == "/.json":
        # Query all documents in the collection and update the results dictionary
        for post in posts.find({}, {'_id': 0}):
            results.update(post)

        # If no results, return 'null'
        if not results:
            return 'null'
    else:
        # Parse the requested path to determine the query path
        x = resp["path"].split("/")
        x = x[1:]
        path = []
        for i in range(len(x) - 1):
            path.append(x[i])

        lastofus = x[-1].split('.')
        if len(lastofus[0]) != 0:
            path.append(lastofus[0])

        currentpath = '.'.join(path)
        startingpoint = path[0]

        # Query documents in the collection based on the specified path
        for post in posts.find({currentpath: {"$exists": True}}, {'_id': 0}):
            results.update(post)

        # If no results, return 'null'
        if not results:
            return 'null'

        # Traverse the results dictionary to the specified path
        for i in path:
            results = results[i]

    # Handle special cases for ordering by "$key" or "$value"
    if orderby == '"$key"':
        if isinstance(results, dict):
            keysList = list(results.keys())
            keysList.sort(key=key_items_cmp)

            # Apply filtering based on startAt, endAt, equalTo, limitToFirst, and limitToLast
            if startat is not None:
                temp = [k for k in keysList if k >= startat[1:-1]]
                keysList = temp
            if endat is not None:
                temp = [k for k in keysList if k <= endat[1:-1]]
                keysList = temp
            if equalto is not None:
                temp = [k for k in keysList if k == equalto[1:-1]]
                keysList = temp
            if limittofirst is not None:
                keysList = keysList[:limittofirst]
            if limittolast is not None:
                keysList = keysList[-limittolast:]

            # Construct a response dictionary based on the ordered keys
            response = {}
            for i in keysList:
                response[i] = results[i]

            results = response

    elif orderby == '"$value"':
        if isinstance(results, dict):
            keysList = list(results.keys())
            haveit = []
            donthaveit = []

            # Separate keys into those with and without a valid value for ordering
            for i in keysList:
                if isinstance(results[i], int) or isinstance(results[i], str) or isinstance(results[i], float):
                    haveit.append([i, results[i]])
                else:
                    donthaveit.append([i])

            # Sort keys with valid values using a custom comparison function
            haveit.sort(key=third_items_cmp)
            keysList = haveit + donthaveit

            # Apply filtering based on startAt, endAt, equalTo, limitToFirst, and limitToLast
            if startat is not None:
                temp = [k for k in keysList if (len(k) == 1) or (k[1] >= startat)]
                keysList = temp
            if endat is not None:
                temp = [k for k in keysList if (len(k) == 1) or (k[1] <= endat)]
                keysList = temp
            if equalto is not None:
                temp = [k for k in keysList if (len(k) == 1) or (k[1] == equalto[1:-1])]
                keysList = temp
            if limittofirst is not None:
                keysList = keysList[:limittofirst]
            if limittolast is not None:
                keysList = keysList[-limittolast:]

            # Construct a response dictionary based on the ordered keys
            response = {}
            for i in keysList:
                response[i[0]] = results[i[0]]

            results = response

    elif orderby is not None:
        if isinstance(results, dict):
            keysList = list(results.keys())
            haveit = []
            donthaveit = []

            # Separate keys into those with and without a valid value for ordering
            for i in keysList:
                if isinstance(results[i], dict) and (orderby[1:-1] in results[i]):
                    if isinstance(results[i][orderby[1:-1]], str) or isinstance(results[i][orderby[1:-1]], int) or isinstance(results[i][orderby[1:-1]], float):
                        haveit.append([i, results[i][orderby[1:-1]]])
                else:
                    donthaveit.append([i])

            # Sort keys with valid values using a custom comparison function
            haveit.sort(key=third_items_cmp)
            keysList = donthaveit + haveit

            # Apply filtering based on startAt, endAt, equalTo, limitToFirst, and limitToLast
            if startat is not None:
                temp = [k for k in keysList if (len(k) == 1) or (k[1] >= startat)]
                keysList = temp
            if endat is not None:
                temp = [k for k in keysList if (len(k) == 1) or (k[1] <= endat)]
                keysList = temp
            if equalto is not None:
                temp = [k for k in keysList if (len(k) == 1) or (k[1] == equalto)]
                keysList = temp
            if limittofirst is not None:
                keysList = keysList[:limittofirst]
            if limittolast is not None:
                keysList = keysList[-limittolast:]

            # Construct a response dictionary based on the ordered keys
            response = {}
            for i in keysList:
                response[i[0]] = results[i[0]]

            results = response

    # Convert the results dictionary to a string and return
    return str(results)


app.run(debug=True)
