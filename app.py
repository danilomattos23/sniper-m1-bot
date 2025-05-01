import os
import time
import requests
import random # Added for potentially better message rotation
from tradingview_ta import TA_Handler, Interval, Exchange
import logging # Added for better logging

# --- Configuration ---
# !!! SET THESE ENVIRONMENT VARIABLES BEFORE RUNNING !!!
# Example (Linux/macOS): export TOKEN="your_bot_token"
# Example (Windows CMD): set TOKEN="your_bot_token"
# Example (Windows PowerShell): $env:TOKEN="your_bot_token"
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
# Ensure MODO_OPERACAO is lowercase for reliable comparison
MODO_OPERACAO = os.getenv("MODO_OPERACAO", "agressivo").lower()
ANALYSIS_INTERVAL = Interval.INTERVAL_1_MINUTE # Make interval easily configurable
ASSET_LOOP_DELAY_SECONDS = 2 # Delay between analysing each asset
FULL_LOOP_DELAY_SECONDS = 30 # Delay after analysing all assets

# --- Logging Setup ---
# Configure logging to show timestamp, level, and message
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Asset Configuration ---
# Define assets and their corresponding screeners/exchanges
# Adjust exchanges based on where you prefer data from and library support
# Common exchanges: FX_IDC, OANDA, FOREXCOM (Forex/CFD)
#                   BINANCE, COINBASE, KRAKEN (Crypto)
ASSET_CONFIG = {
    "EURUSD": {"screener": "forex", "exchange": "FX_IDC"},
    "GBPUSD": {"screener": "forex", "exchange": "FX_IDC"},
    "USDJPY": {"screener": "forex", "exchange": "FX_IDC"},
    "USDCHF": {"screener": "forex", "exchange": "FX_IDC"},
    "AUDUSD": {"screener": "forex", "exchange": "FX_IDC"},
    "BTCUSD": {"screener": "crypto", "exchange": "COINBASE"}, # Specify crypto screener/exchange
    "ETHUSD": {"screener": "crypto", "exchange": "COINBASE"}, # Specify crypto screener/exchange
    "EURJPY": {"screener": "forex", "exchange": "FX_IDC"},
    "GBPJPY": {"screener": "forex", "exchange": "FX_IDC"},
    "NZDUSD": {"screener": "forex", "exchange": "FX_IDC"},
    "USDCAD": {"screener": "forex", "exchange": "FX_IDC"},   # Corrected symbol format
    "EURGBP": {"screener": "forex", "exchange": "FX_IDC"},
    "USDCNH": {"screener": "forex", "exchange": "FX_IDC"},
    "XAUUSD": {"screener": "cfd", "exchange": "OANDA"},      # Use CFD or commodity screener/exchange
}
ATIVOS = list(ASSET_CONFIG.keys())

# --- Telegram Signal Function ---
def enviar_sinal(ativo, direcao):
    """Sends a trading signal message to the configured Telegram chat."""
    if not TOKEN or not CHAT_ID:
        logging.error("TOKEN ou CHAT_ID do Telegram não configurados como variáveis de ambiente.")
        return

    emojis = {"COMPRA": "📈", "VENDA": "📉"}
    mensagens = [
        f"🔥 SINAL FRESQUINHO 🔥\n\n{emojis[direcao]} {direcao} em {ativo}\n⏳ Validade: 1 minuto\nVai nessa que tá bonito 😎",
        f"🚀 OPORTUNIDADE DE {direcao}!\n\nAtivo: {ativo}\nExpiração: 1min\nTaca o dedo que o sinal é quente 🔥",
    ]
    # Use random.choice for variation
    msg = random.choice(mensagens)
    # Original time-based selection (if preferred):
    # msg = mensagens[int(time.time()) % len(mensagens)]

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": msg}

    try:
        response = requests.get(url, params=params, timeout=10) # Added timeout
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        logging.info(f"Sinal de {direcao} para {ativo} enviado com sucesso.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro ao enviar mensagem para Telegram: {e}")
    except Exception as e:
        # Catch any other unexpected errors during the request
        logging.error(f"Erro inesperado ao enviar mensagem para Telegram: {e}")


# --- Asset Analysis Function ---
def analisar_ativo(ativo, config):
    """Analyzes a single asset using TradingView TA and sends a signal if conditions are met."""
    # Moved the print statement here
    logging.info(f"Analisando {ativo} (screener: {config['screener']}, exchange: {config['exchange']})...")

    handler = TA_Handler(
        symbol=ativo,
        screener=config['screener'],
        exchange=config['exchange'],
        interval=ANALYSIS_INTERVAL
    )

    try:
        analise = handler.get_analysis()
        # Safely get indicators, defaulting to None if not found
        rsi = analise.indicators.get("RSI")
        ema9 = analise.indicators.get("EMA9")
        ema21 = analise.indicators.get("EMA21")
        close = analise.indicators.get("close")

        # Crucial check: Ensure all required indicators were successfully retrieved
        if None in [rsi, ema9, ema21, close]:
             logging.warning(f"Não foi possível obter todos os indicadores para {ativo}. Indicadores recebidos: RSI={rsi}, EMA9={ema9}, EMA21={ema21}, Close={close}")
             return # Skip analysis for this asset cycle if data is incomplete

        # Log retrieved indicator values (optional, good for debugging)
        logging.debug(f"{ativo} - RSI: {rsi:.2f}, EMA9: {ema9:.5f}, EMA21: {ema21:.5f}, Close: {close:.5f}")

        sinal = None # Variable to hold the signal direction if conditions met

        # --- Signal Logic ---
        if MODO_OPERACAO == "agressivo":
            if rsi < 35 and ema9 > ema21:
                sinal = "COMPRA"
            elif rsi > 65 and ema9 < ema21:
                sinal = "VENDA"
        # Added 'conservador' as the alternative mode name
        elif MODO_OPERACAO == "conservador":
            # Original conservative logic:
            if rsi < 30 and ema9 > ema21 and close > ema9:
                 sinal = "COMPRA"
            elif rsi > 70 and ema9 < ema21 and close < ema9:
                 sinal = "VENDA"
            # Example of a potentially simpler conservative logic (can be adjusted):
            # if rsi < 30:
            #     sinal = "COMPRA" # Simple oversold
            # elif rsi > 70:
            #     sinal = "VENDA" # Simple overbought
        else:
             # Handle unrecognized MODO_OPERACAO, default to aggressive
             logging.warning(f"MODO_OPERACAO '{MODO_OPERACAO}' não reconhecido. Usando 'agressivo'.")
             if rsi < 35 and ema9 > ema21:
                 sinal = "COMPRA"
             elif rsi > 65 and ema9 < ema21:
                 sinal = "VENDA"
        # --- End Signal Logic ---

        if sinal:
            logging.info(f"Condição de {sinal} detectada para {ativo} (Modo: {MODO_OPERACAO})")
            enviar_sinal(ativo, sinal)
        else:
            # Log if no signal condition was met (can be helpful to know it's checking)
            logging.debug(f"Nenhuma condição de sinal encontrada para {ativo} (Modo: {MODO_OPERACAO})")

    except AttributeError as e:
         # Catch errors if 'indicators' or specific keys are missing from 'analise'
         logging.error(f"Erro de atributo ao processar análise para {ativo} (possivelmente dados ausentes da API ou ativo/exchange inválido): {e}")
    except Exception as e:
        # Catch any other unexpected error during analysis
        logging.error(f"Erro inesperado ao analisar {ativo} ({config['screener']}/{config['exchange']}): {e}")


# --- Main Execution Loop ---
def main():
    """Main function to run the analysis loop."""
    # Critical check for Telegram credentials at the start
    if not TOKEN or not CHAT_ID:
        logging.critical("!!! TOKEN e CHAT_ID do Telegram DEVEM ser definidos como variáveis de ambiente para o script funcionar. Encerrando.")
        return # Stop execution if credentials aren't set

    logging.info(f"--- Iniciando Bot de Sinais TradingView TA ---")
    logging.info(f"Modo de Operação: {MODO_OPERACAO.capitalize()}")
    logging.info(f"Intervalo de Análise: {ANALYSIS_INTERVAL}")
    logging.info(f"Ativos Monitorados: {', '.join(ATIVOS)}")
    logging.info(f"Delay Entre Ativos: {ASSET_LOOP_DELAY_SECONDS}s")
    logging.info(f"Delay Por Ciclo Completo: {FULL_LOOP_DELAY_SECONDS}s")
    logging.info(f"----------------------------------------------")


    while True:
        logging.info("Iniciando novo ciclo de análise de ativos...")
        start_time = time.time()
        for ativo in ATIVOS:
            config = ASSET_CONFIG.get(ativo)
            if config:
                 analisar_ativo(ativo, config)
            else:
                 # This should ideally not happen if ATIVOS is derived from ASSET_CONFIG keys
                 logging.warning(f"Configuração não encontrada para o ativo: {ativo}. Pulando.")

            # Pause between analysing each asset to avoid hitting rate limits
            time.sleep(ASSET_LOOP_DELAY_SECONDS)

        end_time = time.time()
        cycle_duration = end_time - start_time
        logging.info(f"Ciclo de análise concluído em {cycle_duration:.2f} segundos.")

        # Pause after completing a full loop through all assets
        logging.info(f"Aguardando {FULL_LOOP_DELAY_SECONDS} segundos antes do próximo ciclo...")
        time.sleep(FULL_LOOP_DELAY_SECONDS)

# Standard Python entry point guard
if __name__ == "__main__":
    main()
