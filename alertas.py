"""Bot de alertas por Telegram: manda un resumen de precios en cada ejecucion."""
import json
import os
import urllib.parse
import urllib.request

TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

ACTIVOS = {
    "Repsol": "REP.MC",
    "Santander": "SAN.MC",
    "Apple": "AAPL",
    "Tesla": "TSLA",
    "Bitcoin": "BTC-EUR",
}


def obtener_datos(simbolo):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{simbolo}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        meta = json.load(r)["chart"]["result"][0]["meta"]
    precio = float(meta["regularMarketPrice"])
    anterior = meta.get("chartPreviousClose") or meta.get("previousClose")
    moneda = meta.get("currency", "")
    return precio, (float(anterior) if anterior else None), moneda


def enviar(texto):
    datos = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": texto}).encode()
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    urllib.request.urlopen(url, data=datos, timeout=20)


def main():
    lineas = []
    for nombre, simbolo in ACTIVOS.items():
        try:
            precio, anterior, moneda = obtener_datos(simbolo)
            if anterior:
                cambio = (precio - anterior) / anterior * 100
                lineas.append(f"{nombre}: {precio:.2f} {moneda} ({cambio:+.2f}% vs cierre anterior)")
            else:
                lineas.append(f"{nombre}: {precio:.2f} {moneda}")
        except Exception as e:
            print(f"No se pudo obtener el precio de {nombre}: {e}")
            lineas.append(f"{nombre}: sin datos")

    enviar("Resumen de precios\n" + "\n".join(lineas))


if __name__ == "__main__":
    main()
