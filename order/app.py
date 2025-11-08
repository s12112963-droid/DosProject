from flask import Flask, jsonify
import requests

app = Flask(__name__)

# -------------------------
# ROUTES
# -------------------------

@app.route('/purchase/<item_id>', methods=['POST', 'GET'])
def purchase(item_id):
    return jsonify({"message": f"purchase endpoint ready. item={item_id}"}), 200

# -------------------------

# -------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
