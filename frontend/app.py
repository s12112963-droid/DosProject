from flask import Flask, jsonify
import requests

app = Flask(__name__)

# -------------------------
# ROUTES 
# -------------------------

@app.route('/search/<topic>', methods=['GET'])
def fe_search(topic):
    return jsonify({"message": f"frontend search ready. topic={topic}"}), 200

@app.route('/info/<item_id>', methods=['GET'])
def fe_info(item_id):
    return jsonify({"message": f"frontend info ready. item={item_id}"}), 200

@app.route('/purchase/<item_id>', methods=['POST', 'GET'])
def fe_purchase(item_id):
    return jsonify({"message": f"frontend purchase ready. item={item_id}"}), 200

# -------------------------

# -------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
