from flask import Flask, request, jsonify
import csv
from pathlib import Path

app = Flask(__name__)
CATALOG_FILE = Path(__file__).parent / "catalog.csv"

# ---------------------------------------------
# LOAD & SAVE HELPERS
# ---------------------------------------------
def load_catalog():
    items = []
    with open(CATALOG_FILE, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            row["id"] = int(row["id"])
            row["price"] = float(row["price"])
            row["quantity"] = int(row["quantity"])
            items.append(row)
    return items

def save_catalog(items):
    with open(CATALOG_FILE, "w", newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["id","title","topic","price","quantity"])
        writer.writeheader()
        for it in items:
            writer.writerow({
                "id": it["id"],
                "title": it["title"],
                "topic": it["topic"],
                "price": it["price"],
                "quantity": it["quantity"],
            })

def find_item(items, item_id):
    for it in items:
        if it["id"] == item_id:
            return it
    return None

# ---------------------------------------------
# REST ENDPOINTS
# ---------------------------------------------

# GET /search/<topic>
@app.route("/search/<topic>", methods=["GET"])
def search_by_topic(topic):
    items = load_catalog()
    matches = [
        {"id": it["id"], "title": it["title"]}
        for it in items if it["topic"].lower() == topic.lower()
    ]
    return jsonify(matches), 200

# GET /info/<int:item_id>
@app.route("/info/<int:item_id>", methods=["GET"])
def info(item_id):
    items = load_catalog()
    it = find_item(items, item_id)
    if not it:
        return jsonify({"error": "item_not_found"}), 404
    return jsonify({
        "title": it["title"],
        "quantity": it["quantity"],
        "price": it["price"]
    }), 200

# POST /update  
@app.route("/update", methods=["POST"])
def update_item():
    body = request.get_json(silent=True) or {}
    item_id = body.get("item_id")

    if not item_id:
        return jsonify({"error": "missing_item_id"}), 400

    items = load_catalog()
    it = find_item(items, int(item_id))

    if not it:
        return jsonify({"error": "item_not_found"}), 404

  
    if "delta" in body:
        new_q = it["quantity"] + int(body["delta"])
        if new_q < 0:
            return jsonify({"error": "negative_stock_not_allowed"}), 400
        it["quantity"] = new_q


    if "price" in body:
        price = float(body["price"])
        if price < 0:
            return jsonify({"error": "negative_price_not_allowed"}), 400
        it["price"] = price

    save_catalog(items)
    return jsonify({"status": "ok"}), 200

# ---------------------------------------------
# RUN
# ---------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
