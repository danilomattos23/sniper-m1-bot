import telebot
import logging
import time

# === Configurações ===
TOKEN = "8070231977:AAElIGjY3l9EDZaFTvt3nZ71TO7mBWJ0fX8"
CHAT_ID = -1002653453559  # Grupo SinalBinarioBot
bot = telebot.TeleBot(TOKEN)

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
logger.info("Bot de sinais iniciado com sucesso.")

# Estado
status = {"pausado": False}

# === Comandos ===
@bot.message_handler(commands=['status'])
def status_cmd(msg):
    if status["pausado"]:
        bot.reply_to(msg, "⏸ Bot pausado. Nenhum sinal sendo enviado.")
    else:
        bot.reply_to(msg, "▶ Bot ativo e enviando sinais normalmente.")

@bot.message_handler(commands=['pausar'])
def pausar_cmd(msg):
    if not status["pausado"]:
        status["pausado"] = True
        bot.reply_to(msg, "✅ Bot pausado!")
    else:
        bot.reply_to(msg, "ℹ️ O bot já está pausado.")

@bot.message_handler(commands=['retomar'])
def retomar_cmd(msg):
    if status["pausado"]:
        status["pausado"] = False
        bot.reply_to(msg, "✅ Bot retomado! Envio de sinais reativado.")
    else:
        bot.reply_to(msg, "▶️ O bot já está ativo.")

# === Lógica de sinais (exemplo simples) ===
ativos = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD"]

def gerar_sinal_simples(ativo):
    direcao = "COMPRA" if time.time() % 2 == 0 else "VENDA"
    return f"🔥 SINAL FRESQUINHO 🔥\n\nAtivo: {ativo}\nDireção: {direcao}\n⏳ Validade: 1 minuto"

def loop_sinais():
    while True:
        if not status["pausado"]:
            for ativo in ativos:
                sinal = gerar_sinal_simples(ativo)
                try:
                    bot.send_message(CHAT_ID, sinal)
                    logger.info(f"Sinal enviado: {sinal}")
                except Exception as e:
                    logger.error(f"Erro ao enviar sinal: {e}")
                time.sleep(10)  # aguarda entre os sinais
        else:
            logger.info("Bot pausado. Aguardando retomada...")
        time.sleep(30)  # aguarda entre os ciclos

# === Execução ===
def run_bot():
    from threading import Thread
    Thread(target=loop_sinais).start()
    bot.infinity_polling()

if __name__ == "__main__":
    run_bot()
