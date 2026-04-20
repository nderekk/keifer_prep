require('dotenv').config();
const express = require('express');
const cors = require('cors');
const { MongoClient } = require('mongodb');

const app = express();
app.use(cors()); // Allows the frontend to talk to this backend

const uri = process.env.MONGO_URI;
const dbName = process.env.DB_NAME;
const collectionName = process.env.COLLECTION_NAME;

let collection;

// Initialize MongoDB Connection
MongoClient.connect(uri)
    .then(client => {
        console.log('Connected to MongoDB');
        const db = client.db(dbName);
        collection = db.collection(collectionName);
    })
    .catch(error => {
        console.error('Failed to connect to MongoDB', error);
    });

app.get('/api/articles', async (req, res) => {
    try {
        // Fetch articles and project out the _id field
        const articles = await collection.find({}, { projection: { _id: 0 } }).toArray();
        res.json(articles);
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: 'Failed to fetch articles' });
    }
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});