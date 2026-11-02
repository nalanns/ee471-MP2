from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import HTTPException

from custom_classes import Book, DVD, LibraryCollection, ItemNotFoundError, ItemStateError

app = Flask(__name__)

library = LibraryCollection()
library.add_item(Book("Dune", "Frank Herbert", 412))
library.add_item(DVD("The Matrix", "Wachowskis", 136))
library.add_item(Book("The Hobbit", "J.R.R. Tolkien", 310))
library.add_item(DVD("Interstellar", "Christopher Nolan", 169))
library.get_item(2).checkout()


def get_json_body():
    """Return the request body as a dict, or raise ValueError if it is missing or not a JSON object."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object.")
    return data


@app.errorhandler(ValueError)
def handle_value_error(error):
    return jsonify(error=str(error)), 400


@app.errorhandler(ItemNotFoundError)
def handle_not_found(error):
    return jsonify(error=str(error)), 404


@app.errorhandler(ItemStateError)
def handle_state_error(error):
    return jsonify(error=str(error)), 409


@app.errorhandler(HTTPException)
def handle_http_error(error):
    return jsonify(error=error.description), error.code


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/items")
def create_item():
    item = library.create_item(get_json_body())
    return jsonify(item.to_dict()), 201


@app.get("/api/items")
def list_items():
    available = request.args.get("available")
    # Translate the query string to a bool; any other value is passed through and rejected by list_items.
    available = {"true": True, "false": False}.get(available, available)
    items = library.list_items(available=available, item_type=request.args.get("type"))
    return jsonify([item.to_dict() for item in items])


@app.get("/api/items/<int:item_id>")
def get_item(item_id):
    return jsonify(library.get_item(item_id).to_dict())


@app.put("/api/items/<int:item_id>")
def replace_item(item_id):
    library.get_item(item_id)  # 404 before 400 for a missing item
    item = library.replace_item(item_id, **get_json_body())
    return jsonify(item.to_dict())


@app.patch("/api/items/<int:item_id>")
def update_item(item_id):
    library.get_item(item_id)
    item = library.update_item(item_id, **get_json_body())
    return jsonify(item.to_dict())


@app.delete("/api/items/<int:item_id>")
def delete_item(item_id):
    library.remove_item(item_id)
    return "", 204


@app.post("/api/items/<int:item_id>/checkout")
def checkout_item(item_id):
    item = library.get_item(item_id)
    message = item.checkout()
    return jsonify(message=message, item=item.to_dict())


@app.post("/api/items/<int:item_id>/return")
def return_item(item_id):
    item = library.get_item(item_id)
    message = item.return_item()
    return jsonify(message=message, item=item.to_dict())


if __name__ == "__main__":
    app.run(debug=True, port=5000)
