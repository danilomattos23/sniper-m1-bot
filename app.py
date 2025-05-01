import os
import time
import requests
import logging
import json
import pandas as pd
from datetime import datetime

# === Configurações ===
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
ALPHA_KEY = os.getenv("ALPHA_KEY")
MODO_OPERACAO = os.getenv("MODO_OPERACAO", "conservador").lower()

DELAY_ENTRE_ATIVOS = 15
DELAY_CICLO = 60
ARQUIVO_STATUS = "status.json"

ATIVOS = [
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD", "NZDUSD",
    "EURJPY", "GBPJPY", "AUDJPY", "CADJPY", "CHFJPY", "NZDJPY",
    "EURAUD", "EURGBP", "EURNZD", "GBPAUD", "GBPCHF", "GBPNZD", "GBPCAD",
    "USDTRY", "USDZAR", "USDMXN", "USDNOK", "USDSEK", "AUDCAD", "AUDCHF",
    "AUDNZD", "CADCHF", "CHFSGD", "EURCAD", "EURCHF", "EURCZK", "EURDKK",
    "EURHUF", "EURNOK", "EURPLN", "EURSEK", "EURSGD", "EURTRY", "EURZAR",
    "GBPCAD", "GBPNOK", "GBPSGD", "NZDCAD", "NZDCHF", "NZDSGD", "USDHKD"
]

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def carregar_status():
    if not os.path.exists(ARQUIVO_STATUS):
        return {"pausado": False, "sinais_enviados": 0, "ultimo_sinal": None}
    with open(ARQUIVO_STATUS, "r") as f:
        return json.load(f)

def salvar_status(status):
    with open(ARQUIVO_STATUS, "w") as f:
        json.dump(status, f)

status = carregar_status()
def enviar_sinal(ativo, direcao):
    if status.get("pausado"):
        logging.info("Bot pausado. Sinal não enviado.")
        return

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
        status["sinais_enviados"] += 1
        status["ultimo_sinal"] = datetime.now().strftime("%H:%M:%S")
        salvar_status(status)
    except Exception as e:
        logging.error(f"Erro ao enviar sinal: {e}")

def analisar_alpha_vantage(ativo):
    try:
        url = "https://www.alphavantage.co/query"
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
def verificar_comandos():
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
        response = requests.get(url)
        mensagens = response.json().get("result", [])
        if not mensagens:
            return

        for msg in mensagens[-3:]:  # Verifica apenas as últimas 3
            texto = msg.get("message", {}).get("text", "").lower()
            chat_id = msg.get("message", {}).get("chat", {}).get("id")
            if str(chat_id) != CHAT_ID:
                continue

            if texto == "/pausar" and not status.get("pausado"):
                status["pausado"] = True
                salvar_status(status)
                enviar_resposta("⏸️ Bot pausado com sucesso.")

            elif texto == "/retomar" and status.get("pausado"):
                status["pausado"] = False
                salvar_status(status)
                enviar_resposta("▶️ Bot retomado. Sinais serão enviados normalmente.")

            elif texto == "/status":
                resposta = f"""
📊 STATUS DO BOT:
Ativos monitorados: {len(ATIVOS)}
Modo: {MODO_OPERACAO.upper()}
Sinais hoje: {status['sinais_enviados']}
Último sinal: {status['ultimo_sinal'] or "Nenhum ainda"}
Bot pausado: {"✅ Sim" if status.get("pausado") else "❌ Não"}
"""
                enviar_resposta(resposta.strip())
    except Exception as e:
        logging.error(f"Erro ao verificar comandos: {e}")

def enviar_resposta(texto):
    try:
        requests.get(f"https://api.telegram.org/bot{TOKEN}/sendMessage", params={
            "chat_id": CHAT_ID,
            "text": texto
        })
    except:
        pass
def verificar_comandos():
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
        response = requests.get(url)
        mensagens = response.json().get("result", [])
        if not mensagens:
            return

        for msg in mensagens[-3:]:
            texto = msg.get("message", {}).get("text", "").lower()
            chat_id = msg.get("message", {}).get("chat", {}).get("id")
            if str(chat_id) != CHAT_ID:
                continue

            if texto == "/pausar" and not status.get("pausado"):
                status["pausado"] = True
                salvar_status(status)
                enviar_resposta("⏸️ Bot pausado com sucesso.")

            elif texto == "/retomar" and status.get("pausado"):
                status["pausado"] = False
                salvar_status(status)
                enviar_resposta("▶️ Bot retomado. Sinais serão enviados normalmente.")

            elif texto == "/status":
                resposta = f"""
📊 STATUS DO BOT:
Ativos monitorados: {len(ATIVOS)}
Modo: {MODO_OPERACAO.upper()}
Sinais hoje: {status['sinais_enviados']}
Último sinal: {status['ultimo_sinal'] or "Nenhum ainda"}
Bot pausado: {"✅ Sim" if status.get("pausado") else "❌ Não"}
"""
                enviar_resposta(resposta.strip())

        # ✅ Corrige o problema: marca as mensagens como lidas
        ultima_update_id = mensagens[-1]["update_id"]
        requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates", params={"offset": ultima_update_id + 1})

    except Exception as e:
        logging.error(f"Erro ao verificar comandos: {e}")

def main():
    if not TOKEN or not CHAT_ID or not ALPHA_KEY:
        logging.critical("Faltam variáveis de ambiente.")
        return

    logging.info("Bot com controle e comandos iniciado.")

    while True:
        verificar_comandos()# Marcar todas as mensagens como lidas
if mensagens:
    ultima_update_id = mensagens[-1]["update_id"]
    requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates", params={"offset": ultima_update_id + 1})

        if status.get("pausado"):
            logging.info("Bot pausado. Aguardando 30s...")
            time.sleep(30)
            continue

        validos = 0
        for ativo in ATIVOS:
            logging.info(f"Analisando {ativo}...")
            direcao = analisar_alpha_vantage(ativo)
            if direcao:
                enviar_sinal(ativo, direcao)
            else:
                validos += 1
            time.sleep(DELAY_ENTRE_ATIVOS)

        logging.info(f"Ciclo finalizado. Ativos válidos: {validos}. Esperando {DELAY_CICLO}s...")
        time.sleep(DELAY_CICLO)

if __name__ == "__main__":
    main()

