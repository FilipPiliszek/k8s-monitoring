from flask import Flask, request
import time

app = Flask(__name__)


@app.route('/')
def home():
    return (
        "Stress Test App\n\n"
        "CPU:\n"
        "  /cpu/peak   - nagly skok      (Peak Test)    ?seconds=15\n\n"
        "RAM:\n"
        "  /ram/step   - schodkowy wzrost (Step Test)   ?chunks=15&mb=5\n"
        "  /ram/peak   - nagly skok      (Peak Test)    ?mb=80\n"
    )


def burn(seconds):
    """pelne obciazenie CPU przez podana liczbe sekund"""
    end = time.time() + seconds
    while time.time() < end:
        pass


@app.route('/cpu/peak')
def cpu_peak():
    """pelne obciazenie CPU przez X sekund (peak)"""
    seconds = int(request.args.get('seconds', 15))
    burn(seconds)
    return f"CPU PEAK done ({seconds}s)"


@app.route('/ram/step')
def ram_step():
    """alokacja malych porcji co 2s schodkowo"""
    chunks = int(request.args.get('chunks', 15))
    mb = int(request.args.get('mb', 5))
    data = []
    for _ in range(chunks):
        data.append(bytearray(mb * 1024 * 1024))
        time.sleep(2)
    time.sleep(30) # zeby prometeusz zdazyl to zescrapowac
    return f"RAM STEP done (~{chunks * mb} MB)"


@app.route('/ram/peak')
def ram_peak():
    # mb > ~110 przekroczy limit 134MB i wywola OOMKilled (np. ?mb=150).
    mb = int(request.args.get('mb', 80))
    data = bytearray(mb * 1024 * 1024)
    time.sleep(60) # zeby prometeusz zdazyl to zescrapowac
    return f"RAM PEAK done (~{mb} MB)"


if __name__ == "__main__":
    # threaded=True: serwer obsluguje sonde /  rownolegle ze stress-testem,
    # inaczej Kubernetes zabija poda (liveness probe -> connection refused).
    app.run(host="0.0.0.0", port=8080, threaded=True)
