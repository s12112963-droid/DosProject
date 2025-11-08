from flask import Flask, request, jsonify

app = Flask(__name__)

# -------------------------
# ROUTES 
# -------------------------

@app.route('/search/<topic>', methods=['GET'])
def search_books(topic):
    return jsonify({"message": f"search endpoint ready. topic={topic}"}), 200

@app.route('/info/<item_id>', methods=['GET'])
def info(item_id):
    return jsonify({"message": f"info endpoint ready. item_id={item_id}"}), 200

@app.route('/update', methods=['POST'])
def update_book():
    return jsonify({"message": "update endpoint ready"}), 200

# -------------------------

# -------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
