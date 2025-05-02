
# Sniper M1 Bot – Sinais Binários com Estratégia Conservadora

Este é um bot de sinais automáticos para opções binárias, configurado para operar no **modo conservador**, usando análise técnica com **EMA + RSI** para gerar entradas com maior taxa de acerto.

---

## ✅ Como Funciona

O bot analisa os principais pares de moedas (como EURUSD, GBPUSD, etc.) utilizando dados em tempo real com base no gráfico de 1 minuto (M1). A cada ciclo, ele verifica:

- Índice de Força Relativa (**RSI**)
- Médias Móveis Exponenciais (**EMA9** e **EMA21**)
- Confirmação por candle atual

---

## 📊 Critérios para Envio de Sinal

### Compra (CALL):
- RSI abaixo de 30 (**sobrevendido**)
- EMA9 acima da EMA21 (**viés de alta**)
- Fechamento do candle acima da EMA9 (**confirmação**)

### Venda (PUT):
- RSI acima de 70 (**sobrecomprado**)
- EMA9 abaixo da EMA21 (**viés de baixa**)
- Fechamento do candle abaixo da EMA9 (**confirmação**)

---

## 🟢 Exemplo de Sinal

```
🔥 SINAL FRESQUINHO 🔥

Ativo: EURUSD
Direção: COMPRA
⏳ Validade: 1 minuto
⏰ Entrada até: 14:37:00 (horário de Brasília)
```

---

## 🧭 Como Operar com o Sinal

1. Ao receber o sinal, abra sua corretora (IQ Option, Quotex, etc.)
2. Selecione o ativo informado (ex: EURUSD)
3. Escolha a modalidade **Opções Binárias**
4. Configure o tempo de expiração para **1 minuto**
5. Clique em **Compra (verde)** ou **Venda (vermelho)** conforme o sinal

> Importante: o sinal deve ser executado até o horário indicado para funcionar corretamente no próximo candle.
