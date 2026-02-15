from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return "Hello World!"

if __name__ == "__main__":
    app.run(debug=True)   #when running in debug mode, updates will automatically be added to live run of app