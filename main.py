import pandas as pd
import ta
import telebot
import json
import websocket
import threading

# --- 1. CONFIGURACIÓN DEL USUARIO ---
TOKEN_TELEGRAM =8462499394:AAHcpIstq0wJFro0BYHxFlifuIQ90adl6us
CHAT_ID = 6240451923
WSS_URL = wss://api-eu.po.market/socket.io/?EIO=4&transport=websocket

bot = telebot.TeleBot(TOKEN_TELEGRAM)

# Estructura para almacenar velas (Price Action)
data = {
    'time': [], 'open': [], 'high': [], 'low': [], 'close': []
}

# --- 2. LÓGICA DE LA ESTRATEGIA ---
def analizar_mercado():
    df = pd.DataFrame(data)
    if len(df) < 20: return # Necesitamos al menos 20 velas para la EMA

    # Cálculo de Indicadores
    df['ema20'] = ta.trend.ema_indicator(df['close'], window=20)
    vortex = ta.trend.VortexIndicator(df['high'], df['low'], df['close'], window=14)
    df['vi_plus'] = vortex.vortex_indicator_pos()
    df['vi_minus'] = vortex.vortex_indicator_neg()
    df['rsi'] = ta.momentum.rsi(df['close'], window=14)

    # Valores actuales y anteriores para detectar cruces
    last = df.iloc[-1]
    prev = df.iloc[-2]

    # SEÑAL DE COMPRA (CALL)
    # Condiciones: RSI en sobreventa + Cruce Vortex alcista + Precio bajo EMA (Agotamiento)
    if (last['rsi'] < 35) and (last['vi_plus'] > last['vi_minus'] and prev['vi_plus'] < prev['vi_minus']):
        if last['close'] < last['ema20']:
            msg = "🟢 **SEÑAL DE COMPRA (CALL)** 🟢\n" \
                  f"RSI: {round(last['rsi'], 2)}\n" \
                  "Expira: 2 min (Reversión)"
            bot.send_message(CHAT_ID, msg)

    # SEÑAL DE VENTA (PUT)
    # Condiciones: RSI en sobrecompra + Cruce Vortex bajista + Precio sobre EMA (Agotamiento)
    if (last['rsi'] > 65) and (last['vi_minus'] > last['vi_plus'] and prev['vi_minus'] < prev['vi_plus']):
        if last['close'] > last['ema20']:
            msg = "🔴 **SEÑAL DE VENTA (PUT)** 🔴\n" \
                  f"RSI: {round(last['rsi'], 2)}\n" \
                  "Expira: 2 min (Reversión)"
            bot.send_message(CHAT_ID, msg)

# --- 3. CONEXIÓN CON POCKET OPTION ---
def on_message(ws, message):
    # Esta parte procesa los datos reales del broker
    mensaje_json = json.loads(message)
    
    # Aquí el bot extrae el precio de cierre, máximo y mínimo del JSON
    # (El formato varía según el activo, pero esta es la base)
    if "history" in mensaje_json:
        # Lógica para llenar el diccionario 'data' y llamar a analizar_mercado()
        pass

def on_error(ws, error):
    print(f"Error: {error}")

def run_ws():
    ws = websocket.WebSocketApp(WSS_URL, on_message=on_message, on_error=on_error)
    ws.run_forever()

# Iniciar el hilo de conexión
if __name__ == "__main__":
    print("Bot Iniciado y Escuchando...")
    threading.Thread(target=run_ws).start()
