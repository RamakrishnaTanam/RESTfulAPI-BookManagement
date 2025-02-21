import hmac
from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from pymongo import MongoClient
from bson import ObjectId

# Initialize Flask app
app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = "supersecurelongrandomkey123!@#"  # Use env vars in production
api = Api(app)
jwt = JWTManager(app)

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")  # Ensure MongoDB is running
db = client["bookstore"]  # Database name
books_collection = db["books"]
users_collection = db["users"]

# Seed initial data (Run only if collections are empty)
if books_collection.count_documents({}) == 0:
    books_collection.insert_many([
        {"title": "Atomic Habits", "author": "James Clear"},
        {"title": "The Pragmatic Programmer", "author": "Andrew Hunt"},
        {"title": "Deep Work", "author": "Cal Newport"}
    ])

if users_collection.count_documents({}) == 0:
    users_collection.insert_many([
        {"username": "admin", "password": "admin123"},
        {"username": "john_doe", "password": "securepass"},
        {"username": "jane_smith", "password": "password456"}
    ])

class BookList(Resource):
    """Get all books."""
    def get(self):
        books = list(books_collection.find({}, {"_id": 1, "title": 1, "author": 1}))
        for book in books:
            book["_id"] = str(book["_id"])  # Convert ObjectId to string
        return jsonify({"books": books})

class Book(Resource):
    """Get or delete a book by ID."""
    def get(self, book_id):
        book = books_collection.find_one({"_id": ObjectId(book_id)})
        if book:
            book["_id"] = str(book["_id"])
            return jsonify(book)
        return jsonify({"message": "Book not found"}), 404

    @jwt_required()
    def delete(self, book_id):
        result = books_collection.delete_one({"_id": ObjectId(book_id)})
        if result.deleted_count:
            return jsonify({"message": "Book deleted"})
        return jsonify({"message": "Book not found"}), 404

class UserLogin(Resource):
    """Authenticate users and generate JWT token."""
    def post(self):
        data = request.get_json()
        user = users_collection.find_one({"username": data["username"]})
        if user and hmac.compare_digest(user["password"], data["password"]):
            access_token = create_access_token(identity=str(user["_id"]))
            return jsonify({"access_token": access_token})
        return jsonify({"message": "Invalid credentials"}), 401

# Define API routes
api.add_resource(BookList, "/books")
api.add_resource(Book, "/book/<string:book_id>")
api.add_resource(UserLogin, "/login")

if __name__ == "__main__":
    app.run(debug=True)
