from flask import Flask, send_file

app = Flask(__name__, static_folder='static')

@app.route('/')
def home():
    # 접속 시 최상단에 있는 index.html 파일을 화면에 보여줍니다.
    return send_file('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)