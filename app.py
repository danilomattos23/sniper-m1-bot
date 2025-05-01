
import os
import time
import requests
import logging
import yfinance as yf
from tradingview_ta import TA_Handler, Interval
import pandas as pd

# Configurações iniciais
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
MODO_OPERACAO = os.getenv("MODO_OPERACAO", "conservador").lower()

INTERVALO = Interval.INTERVAL_1_MINUTE
DELAY_ENTRE_ATIVOS = 2
DELAY_CICLO = 30

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# +60 ativos binários (Forex + Cripto)
ATIVOS = [
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD", "NZDUSD",
    "EURJPY", "GBPJPY", "AUDJPY", "CADJPY", "CHFJPY", "NZDJPY",
    "EURAUD", "EURGBP", "EURNZD", "GBPAUD", "GBPCHF", "GBPNZD", "GBPCAD",
    "USDTRY", "USDZAR", "USDMXN", "USDNOK", "USDSEK",
    "BTCUSD", "ETHUSD", "LTCUSD", "XRPUSD", "BCHUSD", "SOLUSD", "DOGEUSD"
]

def enviar_sinal(ativo, direcao):
    emojis = {"COMPRA": "📈", "VENDA": "📉"}
    mensagem = f"""
🔥 SINAL DETECTADO 🔥

{emojis[direcao]} {direcao} em {ativo}
⏱️ Validade: 1 minuto
(Modo: {MODO_OPERACAO.upper()})
"""
    try:
        requests.get(f"https://api.telegram.org/bot{TOKEN}/sendMessage", params={
            "chat_id": CHAT_ID,
            "text": mensagem
        })
        logging.info(f"SINAL ENVIADO: {direcao} em {ativo}")
    except Exception as e:
        logging.error(f"Erro ao enviar sinal para Telegram: {e}")

def analisar_com_tradingview(ativo):
    try:
        handler = TA_Handler(
            symbol=ativo,
            screener="crypto" if "USD" in ativo and ativo.startswith(("BTC", "ETH", "XRP", "LTC", "BCH", "DOGE", "SOL")) else "forex",
            exchange="BINANCE" if "USD" in ativo and ativo.startswith(("BTC", "ETH", "XRP", "LTC", "BCH", "DOGE", "SOL")) else "FX_IDC",
            interval=INTERVALO
        )
        analise = handler.get_analysis()
        rsi = analise.indicators.get("RSI")
        ema9 = analise.indicators.get("EMA9")
        ema21 = analise.indicators.get("EMA21")
        close = analise.indicators.get("close")

        if None in [rsi, ema9, ema21, close]:
            raise ValueError("Indicadores incompletos")

        if MODO_OPERACAO == "agressivo":
            if rsi < 35 and ema9 > ema21:
                return "COMPRA"
            elif rsi > 65 and ema9 < ema21:
                return "VENDA"
        else:
            if rsi < 30 and ema9 > ema21 and close > ema9:
                return "COMPRA"
            elif rsi > 70 and ema9 < ema21 and close < ema9:
                return "VENDA"
    except Exception as e:
        logging.warning(f"TradingView falhou para {ativo}: {e}")
        return None

def analisar_com_yfinance(ativo):
    try:
        yf_ativo = ativo + "=X" if not ativo.startswith("BTC") else ativo + "-USD"
        df = yf.download(tickers=yf_ativo, period="1d", interval="1m", progress=False)
        if df.empty or len(df) < 21:
            return None

        close = df["Close"]
        rsi = 100 - (100 / (1 + (close.diff().clip(lower=0).rolling(14).mean() /
                                close.diff().clip(upper=0).abs().rolling(14).mean())))
        ema9 = close.ewm(span=9, adjust=False).mean()
        ema21 = close.ewm(span=21, adjust=False).mean()

        if MODO_OPERACAO == "agressivo":
            if rsi.iloc[-1] < 35 and ema9.iloc[-1] > ema21.iloc[-1]:
                return "COMPRA"
            elif rsi.iloc[-1] > 65 and ema9.iloc[-1] < ema21.iloc[-1]:
                return "VENDA"
        else:
            if rsi.iloc[-1] < 30 and ema9.iloc[-1] > ema21.iloc[-1] and close.iloc[-1] > ema9.iloc[-1]:
                return "COMPRA"
            elif rsi.iloc[-1] > 70 and ema9.iloc[-1] < ema21.iloc[-1] and close.iloc[-1] < ema9.iloc[-1]:
                return "VENDA"
    except Exception as e:
        logging.warning(f"yFinance falhou para {ativo}: {e}")
        return None

def main():
    if not TOKEN or not CHAT_ID:
        logging.critical("TOKEN e CHAT_ID não configurados.")
        return

    logging.info("Bot iniciado com múltiplas fontes de análise.")
    while True:
        for ativo in ATIVOS:
            logging.info(f"Analisando {ativo}...")
            direcao = analisar_com_tradingview(ativo)
            if not direcao:
                direcao = analisar_com_yfinance(ativo)
            if direcao:
                enviar_sinal(ativo, direcao)
            time.sleep(DELAY_ENTRE_ATIVOS)
        logging.info(f"Ciclo completo. Aguardando {DELAY_CICLO}s...")
        time.sleep(DELAY_CICLO)

if __name__ == "__main__":
    main()
