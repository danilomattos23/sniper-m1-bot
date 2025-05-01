import os
import time
import requests
from tradingview_ta import TA_Handler, Interval, Exchange

# Configurações do Telegram
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
MODO_OPERACAO = os.getenv("MODO_OPERACAO", "agressivo")

# Lista de ativos populares
ATIVOS = [
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "BTCUSD", "ETHUSD",
    "EURJPY", "GBPJPY", "NZDUSD", "USD/CAD", "EURGBP", "USDCNH", "XAUUSD"
]

def enviar_sinal(ativo, direcao):
    emojis = {
        "COMPRA": "📈",
        "VENDA": "📉"
    }
    mensagens = [
        f"🔥 SINAL FRESQUINHO 🔥\n\n{emojis[direcao]} {direcao} em {ativo}\n⏳ Validade: 1 minuto\nVai nessa que tá bonito 😎",
        f"🚀 OPORTUNIDADE DE {direcao}!\n\nAtivo: {ativo}\nExpiração: 1min\nTaca o dedo que o sinal é quente 🔥",
    ]
    msg = mensagens[int(time.time()) % len(mensagens)]
    requests.get(f"https://api.telegram.org/bot{TOKEN}/sendMessage", params={
        "chat_id": CHAT_ID,
        "text": msg
    })

def analisar_ativo(ativo):
    handler = TA_Handler(
        symbol=ativo,
        screener="forex",
        exchange="FX_IDC",
        interval=Interval.INTERVAL_1_MINUTE
    )
    try:
        analise = handler.get_analysis()
        rsi = analise.indicators["RSI"]
        ema9 = analise.indicators["EMA9"]
        ema21 = analise.indicators["EMA21"]
        close = analise.indicators["close"]

        if MODO_OPERACAO == "agressivo":
            if rsi < 35 and ema9 > ema21:
                enviar_sinal(ativo, "COMPRA")
            elif rsi > 65 and ema9 < ema21:
                enviar_sinal(ativo, "VENDA")
        else:
            if rsi < 30 and ema9 > ema21 and close > ema9:
                enviar_sinal(ativo, "COMPRA")
            elif rsi > 70 and ema9 < ema21 and close < ema9:
                enviar_sinal(ativo, "VENDA")

    except Exception as e:
        print(f"Erro ao analisar {ativo}: {e}")

# Loop infinito de análise
while True:
    for ativo in ATIVOS:
        analisar_ativo(ativo)
        time.sleep(2)  # evita sobrecarga e limites de API
    time.sleep(30)
