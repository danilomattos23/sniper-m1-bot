import os
import time
import requests
import logging
import pandas as pd

# === Configurações ===
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
ALPHA_KEY = os.getenv("ALPHA_KEY")
MODO_OPERACAO = os.getenv("MODO_OPERACAO", "conservador").lower()

DELAY_ENTRE_ATIVOS = 15
DELAY_CICLO = 60

# Ativos Forex
ATIVOS = [
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD", "NZDUSD",
    "EURJPY", "GBPJPY", "AUDJPY", "CADJPY", "CHFJPY", "NZDJPY",
    "EURAUD", "EURGBP", "EURNZD", "GBPAUD", "GBPCHF", "GBPNZD", "GBPCAD",
    "USDTRY", "USDZAR", "USDMXN", "USDNOK", "USDSEK", "AUDCAD", "AUDCHF",
    "AUDNZD", "CADCHF", "CHFSGD", "EURCAD", "EURCHF", "EURCZK", "EURDKK",
    "EURHUF", "EURNOK", "EURPLN", "EURSEK", "EURSGD", "EURTRY", "EURZAR",
    "GBPCAD", "GBPNOK", "GBPSGD", "NZDCAD", "NZDCHF", "NZDSGD", "USDHKD"
]

# Setup de logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# === Envio para Telegram ===
def enviar_sinal(ativo, direcao):
    msg = f"""
🔥 SINAL DETECTADO 🔥
📊 {direcao} em {ativo}
⏱️ Validade: 1 minuto
(Modo: {MODO_OPERACAO.upper()})
"""
    try:
        requests.get(f"https://api.telegram.org/bot{TOKEN}/sendMessage", params={
            "chat_id": CHAT_ID,
            "text": msg
        })
        logging.info(f"SINAL ENVIADO: {direcao} em {ativo}")
    except Exception as e:
        logging.error(f"Erro ao enviar sinal: {e}")

# === Análise com Alpha Vantage ===
def analisar_alpha_vantage(ativo):
    try:
        url = f"https://www.alphavantage.co/query"
        params = {
            "function": "FX_INTRADAY",
            "from_symbol": ativo[:3],
            "to_symbol": ativo[3:],
            "interval": "1min",
            "apikey": ALPHA_KEY,
            "outputsize": "compact"
        }
        response = requests.get(url, params=params)
        data = response.json()

        if "Time Series FX (1min)" not in data:
            logging.warning(f"Alpha Vantage sem dados para {ativo}")
            return None

        df = pd.DataFrame.from_dict(data["Time Series FX (1min)"], orient="index").astype(float)
        df = df.rename(columns={
            "1. open": "Open",
            "2. high": "High",
            "3. low": "Low",
            "4. close": "Close"
        }).sort_index()

        close = df["Close"]
        if len(close) < 21:
            return None

        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(14).mean()
        avg_loss = loss.rolling(14).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
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
        return None
    except Exception as e:
        logging.error(f"Erro ao analisar {ativo}: {e}")
        return None

# === Loop Principal ===
def main():
    if not TOKEN or not CHAT_ID or not ALPHA_KEY:
        logging.critical("Faltam variáveis de ambiente.")
        return

    logging.info("Bot de sinais Alpha Vantage iniciado.")
    while True:
        for ativo in ATIVOS:
            logging.info(f"Analisando {ativo}...")
            direcao = analisar_alpha_vantage(ativo)
            if direcao:
                enviar_sinal(ativo, direcao)
            time.sleep(DELAY_ENTRE_ATIVOS)
        logging.info(f"Fim do ciclo. Aguardando {DELAY_CICLO}s...")
        time.sleep(DELAY_CICLO)

if __name__ == "__main__":
    main()
