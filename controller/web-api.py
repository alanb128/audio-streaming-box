from flask import Flask, jsonify, request# initialize our Flask application
app= Flask(__name__)@app.route("/name", methods=["POST"])
def setName():
    if request.method=='POST':
        posted_data = request.get_json()
        data = posted_data['data']
        return jsonify(str("Successfully stored  " + str(data)))@app.route("/message", methods=["GET"])
def message():
    posted_data = request.get_json()
    name = posted_data['name']
    return jsonify(" Hope you are having a good time " +  name + "!!!")#  main thread of execution to start the server
if __name__=='__main__':
    app.run(debug=True)
