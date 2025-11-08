from flask import Flask, jsonify
import requests

app = Flask(__name__)

CATALOG_URL = "http://localhost:5001"

# ------------------------------------------------
# PURCHASE ENDPOINT
# ------------------------------------------------
@app.route('/purchase/<int:item_id>', methods=['POST', 'GET'])
def purchase(item_id):
    
    info_url = f"{CATALOG_URL}/info/{item_id}"
    info_response = requests.get(info_url)

    if info_response.status_code == 404:
        return jsonify({"error": "item_not_found"}), 404

    info_data = info_response.json()

    quantity = info_data["quantity"]

    if quantity == 0:
        return jsonify({"error": "out_of_stock"}), 400

    update_url = f"{CATALOG_URL}/update"
    update_body = {
        "item_id": item_id,
        "delta": -1
    }

    update_response = requests.post(update_url, json=update_body)

    if update_response.status_code != 200:
        return jsonify({"error": "update_failed"}), 500

    return jsonify({
        "status": "success",
        "message": f"bought book {info_data['title']}"
    }), 200

# ------------------------------------------------
# RUN SERVICE
# ------------------------------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
