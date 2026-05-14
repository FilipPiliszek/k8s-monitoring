from flask import Flask
import time

app = Flask(__name__)

@app.route('/')
def home():
    return "Wszystko smiga dodaj do adresu /stress-cpu albo /stress-ram"

@app.route('/stress-cpu')
def stress_cpu():
    timeout = time.time() + 15
    while time.time() < timeout:
        pass
    return "Koniec obciazenia cpu"

@app.route('/stress-ram')
def stress_ram():
    timeout = time.time() + 15
    a = []
    for _ in range(50):
        a.append('a' * 10**6)
    time.sleep(15)
    return "Koniec obciazenia ram"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

