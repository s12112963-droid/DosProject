from flask import Flask, jsonify, request
import requests
import os
import csv
from pathlib import Path
from datetime import datetime

app = Flask(__name__)

CATALOG_REPLICAS = [
    u.strip() for u in os.getenv(
        "CATALOG_REPLICAS", "http://localhost:5001,http://localhost:5003"
    ).split(",") if u.strip()
]

ORDER_PEERS = [
    u.strip() for u in os.getenv("ORDER_PEERS", "").split(",") if u.strip()
]

HTTP_TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "10"))

ORDERS_FILE = Path(__file__).parent / "orders.csv"
_rr = 0


def pick_catalog():
    global _rr
    url = CATALOG_REPLICAS[_rr % len(CATALOG_REPLICAS)]
    _rr += 1
    return url


def ensure_orders_file():
    if not ORDERS_FILE.exists():
        with open(ORDERS_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f, fieldnames=["order_id", "item_id", "title", "price", "timestamp"]
            )
            writer.writeheader()


def next_order_id():
    ensure_orders_file()
    with open(ORDERS_FILE, newline="", encoding="utf-8") as f:
        return len(list(csv.DictReader(f))) + 1


def append_order(row):
    ensure_orders_file()
    with open(ORDERS_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["order_id", "item_id", "title", "price", "timestamp"]
        )
        writer.writerow(row)


def forward_to_peers(row):
    for peer in ORDER_PEERS:
        try:
            requests.post(
                f"{peer}/replica-order", json=row, timeout=HTTP_TIMEOUT
            )
        except:
            pass


@app.route("/purchase/<int:item_id>", methods=["POST", "GET"])
def purchase(item_id):
    catalog = pick_catalog()

    try:
        info = requests.get(
            f"{catalog}/info/{item_id}", timeout=HTTP_TIMEOUT
        )
    except Exception as e:
        return jsonify({"error": "catalog_unreachable", "details": str(e)}), 500

    if info.status_code != 200:
        return jsonify({"error": "item_not_found"}), 404

    data = info.json()
    if data["quantity"] <= 0:
        return jsonify({"error": "out_of_stock"}), 400

    try:
        upd = requests.post(
            f"{catalog}/update",
            json={"item_id": item_id, "delta": -1},
            timeout=HTTP_TIMEOUT,
        )
    except Exception as e:
        return jsonify({"error": "update_failed", "details": str(e)}), 500

    if upd.status_code != 200:
        return jsonify({"error": "update_failed"}), 500

    row = {
        "order_id": next_order_id(),
        "item_id": item_id,
        "title": data["title"],
        "price": data["price"],
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    append_order(row)
    forward_to_peers(row)

    return jsonify({"status": "success", "order": row}), 200


@app.route("/replica-order", methods=["POST"])
def replica_order():
    body = request.get_json(silent=True) or {}
    append_order(body)
    return jsonify({"status": "replica_logged"}), 200


@app.route("/orders", methods=["GET"])
def orders():
    ensure_orders_file()
    with open(ORDERS_FILE, newline="", encoding="utf-8") as f:
        return jsonify(list(csv.DictReader(f))), 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5002"))
    app.run(host="0.0.0.0", port=port)
