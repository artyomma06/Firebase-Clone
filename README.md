# Firebase API clone with MongoDB Cloud Integration

Welcome to the *Firebase API clone with MongoDB Cloud Integration* project! This project is a full clone of the firebase api allowing the someone to launch it and make api requests as if it was a firebase server. The requests are all stored on the cloud using MongoDB Atlas.

## Implementation

The project uses the Flask Framework to and can handle several HTTP methods:

1. **GET Method:**
   - Retrieves data from the MongoDB collection based on the requested path and query parameters.
   - Supports ordering, limiting, starting, ending, and equality filtering.

2. **POST Method:**
   - Inserts data into the collection based on the requested path and payload.
   - Generates a unique identifier for each inserted document.

3. **PATCH Method:**
   - Updates existing data in the collection based on the requested path and payload.
   - Supports partial updates and insertion if the specified path does not exist.

4. **DELETE Method:**
   - Deletes data from the collection based on the requested path.
   - Supports deletion of documents and specific fields within documents.

## Prerequisites

To set up and run this project, make sure you have the following:

- Python installed on your system.
- Flask library installed (`pip install Flask`).
- Mongo db library installed(`pip install pymongo`).
- Mongo atlas instance running with api key.
- An understanding of REST API concepts.

## Usage

1. **Clone the Repository:**
   - Clone this repository to your local machine.

2. **Run the Server:**
   - Execute the main Python script to run the Flask server(`python server.py`).

3. **Explore API Endpoints:**
   - Use your preferred API client (e.g., Postman, curl) to send requests to different endpoints.
   - Customize requests based on the implemented functions for GET, POST, PATCH, and DELETE.

4. **Interact with MongoDB:**
   - Observe how the server interacts with the MongoDB 'posts' collection.
   - Experiment with different paths, query parameters, and payload formats.