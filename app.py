import os
import time
import requests
import random
from tradingview_ta import TA_Handler, Interval
import logging

# --- Configurações Iniciais ---
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
MODO_OPERACAO = os.getenv("MODO_OPERACAO", "agressivo").lower()

ANALYSIS_INTERVAL = Interval.INTERVAL_1_MINUTE
ASSET_LOOP_DELAY_SECONDS = 2
FULL_LOOP_DELAY_SECONDS = 30

# --- Setup de Logs ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Lista de Ativos com Exchanges ---
ASSET_CONFIG = {
    "EURUSD": {"screener": "forex", "exchange": "FX_IDC"},
    "GBPUSD": {"screener": "forex", "exchange": "FX_IDC"},
    "USDJPY": {"screener": "forex", "exchange": "FX_IDC"},
    "USDCHF": {"screener": "forex", "exchange": "FX_IDC"},
    "AUDUSD": {"screener": "forex", "exchange": "FX_IDC"},
    "BTCUSD": {"screener": "crypto", "exchange": "COINBASE"},
    "ETHUSD": {"screener": "crypto", "exchange": "COINBASE"},
    "EURJPY": {"screener": "forex", "exchange": "FX_IDC"},
    "GBPJPY": {"screener": "forex", "exchange": "FX_IDC"},
    "NZDUSD": {"screener": "forex", "exchange": "FX_IDC"},
    "USDCAD": {"screener": "forex", "exchange": "FX_IDC"},
    "EURGBP": {"screener": "forex", "exchange": "FX_IDC"},
    "USDCNH": {"screener": "forex", "exchange": "FX_IDC"},
    "XAUUSD": {"screener": "cfd", "exchange": "OANDA"},
}
ATIVOS = list(ASSET_CONFIG.keys())

# --- Função para Enviar Sinal no Telegram ---
def enviar_sinal(ativo, direcao):
    if not TOKEN or not CHAT_ID:
        logging.error("TOKEN ou CHAT_ID não configurados.")
        return

    emojis = {"COMPRA": "📈", "VENDA": "📉"}
    mensagens = [
        f"🔥 SINAL FRESQUINHO 🔥\n\n{emojis[direcao]} {direcao} em {ativo}\n⏳ Validade: 1 minuto\nVai nessa que tá bonito 😎",
        f"🚀 OPORTUNIDADE DE {direcao}!\n\nAtivo: {ativo}\nExpiração: 1min\nTaca o dedo que o sinal é quente 🔥",
    ]
    msg = random.choice(mensagens)

    try:
        response = requests.get(f"https://api.telegram.org/bot{TOKEN}/sendMessage", params={
            "chat_id": CHAT_ID,
            "text": msg
        }, timeout=10)
        response.raise_for_status()
        logging.info(f"Sinal de {direcao} para {ativo} enviado com sucesso.")
    except Exception as e:
        logging.error(f"Erro ao enviar sinal: {e}")

# --- Análise Técnica de Cada Ativo ---
def analisar_ativo(ativo, config):
    logging.info(f"Analisando {ativo}...")

    handler = TA_Handler(
        symbol=ativo,
        screener=config['screener'],
        exchange=config['exchange'],
        interval=ANALYSIS_INTERVAL
    )

    try:
        analise = handler.get_analysis()
        rsi = analise.indicators.get("RSI")
        ema9 = analise.indicators.get("EMA9")
        ema21 = analise.indicators.get("EMA21")
        close = analise.indicators.get("close")

        if None in [rsi, ema9, ema21, close]:
            logging.warning(f"Indicadores incompletos para {ativo}.")
            return

        sinal = None

        if MODO_OPERACAO == "agressivo":
            if rsi < 35 and ema9 > ema21:
                sinal = "COMPRA"
            elif rsi > 65 and ema9 < ema21:
                sinal = "VENDA"
        elif MODO_OPERACAO == "conservador":
            if rsi < 30 and ema9 > ema21 and close > ema9:
                sinal = "COMPRA"
            elif rsi > 70 and ema9 < ema21 and close < ema9:
                sinal = "VENDA"
        else:
            logging.warning(f"Modo '{MODO_OPERACAO}' inválido. Usando agressivo.")
            if rsi < 35 and ema9 > ema21:
                sinal = "COMPRA"
            elif rsi > 65 and ema9 < ema21:
                sinal = "VENDA"

        if sinal:
            logging.info(f"Sinal detectado: {sinal} em {ativo}")
            enviar_sinal(ativo, sinal)
        else:
            logging.debug(f"Nenhum sinal em {ativo}")

    except Exception as e:
        logging.error(f"Erro ao analisar {ativo}: {e}")

# --- Loop Principal ---
def main():
    if not TOKEN or not CHAT_ID:
        logging.critical("TOKEN e CHAT_ID são obrigatórios.")
        return

    logging.info(f"Iniciando SniperM1 Bot em modo '{MODO_OPERACAO}'")

    while True:
        for ativo in ATIVOS:
            config = ASSET_CONFIG[ativo]
            analisar_ativo(ativo, config)
            time.sleep(ASSET_LOOP_DELAY_SECONDS)

        logging.info(f"Aguardando {FULL_LOOP_DELAY_SECONDS}s para próximo ciclo...")
        time.sleep(FULL_LOOP_DELAY_SECONDS)

if __name__ == "__main__":
    main()
