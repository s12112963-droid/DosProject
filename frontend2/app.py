from flask import Flask, jsonify, request
import requests
import os
from collections import OrderedDict

app = Flask(__name__)

CATALOG_REPLICAS = [
    u.strip() for u in os.getenv(
        "CATALOG_REPLICAS", "http://localhost:5001,http://localhost:5003"
    ).split(",") if u.strip()
]

ORDER_REPLICAS = [
    u.strip() for u in os.getenv(
        "ORDER_REPLICAS", "http://localhost:5002"
    ).split(",") if u.strip()
]

HTTP_TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "15"))
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "1") == "1"
CACHE_CAPACITY = 50

catalog_rr = 0
order_rr = 0
cache = OrderedDict()


def pick_catalog():
    global catalog_rr
    url = CATALOG_REPLICAS[catalog_rr % len(CATALOG_REPLICAS)]
    catalog_rr += 1
    return url


def pick_order():
    global order_rr
    url = ORDER_REPLICAS[order_rr % len(ORDER_REPLICAS)]
    order_rr += 1
    return url


@app.route("/search/<topic>", methods=["GET"])
def search(topic):
    url = pick_catalog()
    r = requests.get(f"{url}/search/{topic}", timeout=HTTP_TIMEOUT)
    return jsonify(r.json()), r.status_code


@app.route("/info/<int:item_id>", methods=["GET"])
def info(item_id):
    key = f"info:{item_id}"

    if CACHE_ENABLED and key in cache:
        return jsonify({**cache[key], "source": "cache"}), 200

    url = pick_catalog()
    r = requests.get(f"{url}/info/{item_id}", timeout=HTTP_TIMEOUT)
    if r.status_code != 200:
        return jsonify(r.json()), r.status_code

    data = r.json()
    data["source"] = url

    if CACHE_ENABLED:
        cache[key] = data
        if len(cache) > CACHE_CAPACITY:
            cache.popitem(last=False)

    return jsonify(data), 200


@app.route("/invalidate", methods=["POST"])
def invalidate():
    body = request.get_json(silent=True) or {}
    item_id = body.get("item_id")
    if item_id:
        cache.pop(f"info:{item_id}", None)
    return jsonify({"status": "ok"}), 200


@app.route("/cache-status", methods=["GET"])
def cache_status():
    return jsonify(
        {
            "enabled": CACHE_ENABLED,
            "capacity": CACHE_CAPACITY,
            "size": len(cache),
            "keys": list(cache.keys()),
        }
    ), 200


@app.route("/purchase/<int:item_id>", methods=["POST", "GET"])
def purchase(item_id):
    try:
        url = pick_order()
        r = requests.post(
            f"{url}/purchase/{item_id}", timeout=HTTP_TIMEOUT
        )
        return jsonify({**r.json(), "source": url}), r.status_code
    except Exception as e:
        return jsonify(
            {
                "error": "order_unreachable",
                "details": str(e),
                "order_replicas": ORDER_REPLICAS,
            }
        ), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
