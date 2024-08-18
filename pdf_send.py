from flask import Flask, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/get-pdf',methods=['GET'])
def get_pdf():
    file_path = r'C:\Users\hirokikawai\Downloads\final_exam.pdf'
    return send_file(file_path,as_attachment=False)

if __name__ == '__main__':
    app.run(debug=True, host='192.168.3.114', port=5000)