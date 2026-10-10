"""Bot de alertas de precios por Telegram.

Avisa cuando Repsol, Santander, Apple, Tesla o Bitcoin se mueven mas de UMBRAL %
desde el ultimo aviso. El token y el chat id vienen de variables de entorno
(GitHub Secrets), nunca van escritos en el codigo.
"""
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

UMBRAL = 1.0  # % de cambio minimo para avisar

TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
ESTADO = Path(__file__).with_name("estado.json")

ACTIVOS = {
    "Repsol": "REP.MC",
    "Santander": "SAN.MC",
    "Apple": "AAPL",
    "Tesla": "TSLA",
    "Bitcoin": "BTC-EUR",
}


def obtener_precio(simbolo):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{simbolo}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        meta = json.load(r)["chart"]["result"][0]["meta"]
    return float(meta["regularMarketPrice"]), meta.get("currency", "")


def enviar(texto):
    datos = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": texto}).encode()
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    urllib.request.urlopen(url, data=datos, timeout=20)


def main():
    ultimo = json.loads(ESTADO.read_text()) if ESTADO.exists() else {}

    for nombre, simbolo in ACTIVOS.items():
        try:
            precio, moneda = obtener_precio(simbolo)
        except Exception as e:
            print(f"No se pudo obtener el precio de {nombre}: {e}")
            continue

        # Primera ejecucion: solo guarda el precio de referencia
        if nombre not in ultimo:
            ultimo[nombre] = precio
            continue

        cambio = (precio - ultimo[nombre]) / ultimo[nombre] * 100
        if abs(cambio) >= UMBRAL:
            direccion = "SUBE" if cambio > 0 else "BAJA"
            texto = f"{nombre} {direccion} {cambio:+.2f}%\n{ultimo[nombre]:.2f} -> {precio:.2f} {moneda}"
            try:
                enviar(texto)
                ultimo[nombre] = precio
            except Exception as e:
                print(f"No se pudo enviar el mensaje de Telegram: {e}")

    ESTADO.write_text(json.dumps(ultimo, indent=2))


if __name__ == "__main__":
    main()
