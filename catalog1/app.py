from flask import Flask, request, jsonify
import csv
import os
import requests
from pathlib import Path

app = Flask(__name__)

PORT = int(os.getenv("PORT", "5001"))
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5000")
CATALOG_PEERS = [
    u.strip() for u in os.getenv("CATALOG_PEERS", "").split(",") if u.strip()
]
HTTP_TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "0.2"))

CATALOG_FILE = Path(__file__).parent / "catalog.csv"


def load_catalog():
    items = []
    with open(CATALOG_FILE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            row["id"] = int(row["id"])
            row["price"] = float(row["price"])
            row["quantity"] = int(row["quantity"])
            items.append(row)
    return items


def save_catalog(items):
    with open(CATALOG_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["id", "title", "topic", "price", "quantity"]
        )
        writer.writeheader()
        for it in items:
            writer.writerow(it)


def find_item(items, item_id):
    for it in items:
        if it["id"] == item_id:
            return it
    return None


@app.route("/search/<topic>", methods=["GET"])
def search(topic):
    items = load_catalog()
    res = [
        {"id": it["id"], "title": it["title"]}
        for it in items
        if it["topic"].lower() == topic.lower()
    ]
    return jsonify(res), 200


@app.route("/info/<int:item_id>", methods=["GET"])
def info(item_id):
    items = load_catalog()
    it = find_item(items, item_id)
    if not it:
        return jsonify({"error": "item_not_found"}), 404
    return jsonify(
        {"title": it["title"], "price": it["price"], "quantity": it["quantity"]}
    ), 200


@app.route("/update", methods=["POST"])
def update():
    body = request.get_json(silent=True) or {}
    item_id = body.get("item_id")
    if not item_id:
        return jsonify({"error": "missing_item_id"}), 400

    items = load_catalog()
    it = find_item(items, int(item_id))
    if not it:
        return jsonify({"error": "item_not_found"}), 404

    try:
        requests.post(
            f"{FRONTEND_URL}/invalidate",
            json={"item_id": item_id},
            timeout=HTTP_TIMEOUT,
        )
    except:
        pass

    if "delta" in body:
        new_q = it["quantity"] + int(body["delta"])
        if new_q < 0:
            return jsonify({"error": "negative_stock"}), 400
        it["quantity"] = new_q

    if "price" in body:
        price = float(body["price"])
        if price < 0:
            return jsonify({"error": "negative_price"}), 400
        it["price"] = price

    save_catalog(items)

    for peer in CATALOG_PEERS:
        try:
            requests.post(
                f"{peer}/replica-update", json=body, timeout=HTTP_TIMEOUT
            )
        except:
            pass

    return jsonify({"status": "ok"}), 200


@app.route("/replica-update", methods=["POST"])
def replica_update():
    body = request.get_json(silent=True) or {}
    item_id = body.get("item_id")
    if not item_id:
        return jsonify({"error": "missing_item_id"}), 400

    items = load_catalog()
    it = find_item(items, int(item_id))
    if not it:
        return jsonify({"error": "item_not_found"}), 404

    if "delta" in body:
        it["quantity"] += int(body["delta"])

    if "price" in body:
        it["price"] = float(body["price"])

    save_catalog(items)
    return jsonify({"status": "replica_ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
