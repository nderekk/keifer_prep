from flask import Flask, jsonify
from flask_cors import CORS
from pymongo import MongoClient

app = Flask(__name__)
CORS(app)  # Allows your frontend to talk to this backend

# MongoDB Connection
client = MongoClient("mongodb://localhost:27017/")
db = client["prep_database"]
collection = db["articles"]

@app.route('/api/articles', methods=['GET'])
def get_articles():
    # Pull articles from Mongo and convert ObjectId to string
    articles = list(collection.find({}, {'_id': 0}))
    return jsonify(articles)

if __name__ == '__main__':
    app.run(debug=True, port=5000)