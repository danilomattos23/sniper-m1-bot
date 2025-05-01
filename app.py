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
