from flask import Flask, jsonify
import requests

app = Flask(__name__)


CATALOG_URL = "http://localhost:5001"
ORDER_URL = "http://localhost:5002"

# ------------------------------------------------
# SEARCH ENDPOINT
# ------------------------------------------------
@app.route('/search/<topic>', methods=['GET'])
def fe_search(topic):
    try:
        response = requests.get(f"{CATALOG_URL}/search/{topic}")
        return jsonify(response.json()), response.status_code
    except:
        return jsonify({"error": "catalog_unreachable"}), 500


# ------------------------------------------------
# INFO ENDPOINT
# ------------------------------------------------
@app.route('/info/<int:item_id>', methods=['GET'])
def fe_info(item_id):
    try:
        response = requests.get(f"{CATALOG_URL}/info/{item_id}")
        return jsonify(response.json()), response.status_code
    except:
        return jsonify({"error": "catalog_unreachable"}), 500


# ------------------------------------------------
# PURCHASE ENDPOINT
# ------------------------------------------------
@app.route('/purchase/<int:item_id>', methods=['POST', 'GET'])
def fe_purchase(item_id):
    try:
        response = requests.post(f"{ORDER_URL}/purchase/{item_id}")
        return jsonify(response.json()), response.status_code
    except:
        return jsonify({"error": "order_unreachable"}), 500


# ------------------------------------------------
# RUN SERVICE
# ------------------------------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
