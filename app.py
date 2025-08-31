from flask import Flask, request, jsonify
from datetime import datetime
import os, csv

from config import SETTINGS
from binance_client import BinanceUMFutures

app = Flask(__name__)

# 初始化幣安客戶端（指向測試網）
client = BinanceUMFutures(
    api_key=SETTINGS["BINANCE_API_KEY"],
    api_secret=SETTINGS["BINANCE_API_SECRET"],
    base_url=SETTINGS["BINANCE_UMF_BASE"],
)

# 設定交易模式
def ensure_trading_prefs(symbol: str, leverage: int, dual_side: bool=True):
    client.set_position_mode(dualSide=dual_side)
    client.set_leverage(symbol=symbol, leverage=leverage)

# 紀錄交易
def log_trade(payload: dict, resp: dict):
    os.makedirs("logs", exist_ok=True)
    path = os.path.join("logs", "trades.csv")
    headers = ["ts","symbol","side","positionSide","orderType","qty","sl","tp","leverage","resp"]
    write_header = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if write_header: w.writerow(headers)
        w.writerow([
            datetime.utcnow().isoformat(),
            payload.get("symbol"), payload.get("side"),
            payload.get("positionSide"), payload.get("orderType"),
            payload.get("amount"), payload.get("stopLoss"),
            payload.get("takeProfit"), payload.get("leverage"),
            resp,
        ])

@app.get("/health")
def health():
    return {"ok": True, "time": datetime.utcnow().isoformat()}

@app.post("/webhook")
def webhook():
    secret = request.headers.get("X-Webhook-Secret") or request.args.get("secret")
    if secret != SETTINGS["WEBHOOK_SECRET"]:
        return jsonify({"ok": False, "error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    symbol       = data.get("symbol","ETHUSDT").upper()
    side         = data.get("side","BUY").upper()
    positionSide = data.get("positionSide","LONG").upper()
    orderType    = data.get("orderType","MARKET").upper()
    qty          = float(data.get("amount",0.01))
    leverage     = int(data.get("leverage",10))
    sl_price     = data.get("stopLoss")
    tp_price     = data.get("takeProfit")
    marginType   = data.get("marginType","CROSSED").upper()

    try:
        ensure_trading_prefs(symbol, leverage, dual_side=True)
        client.set_margin_type(symbol=symbol, marginType=marginType)

        r_open = client.create_order(
            symbol=symbol, side=side, positionSide=positionSide,
            type=orderType, quantity=qty,
        )

        r_sl = r_tp = None
        if sl_price:
            r_sl = client.create_order(
                symbol=symbol,
                side=("SELL" if positionSide=="LONG" else "BUY"),
                positionSide=positionSide,
                type="STOP_MARKET",
                stopPrice=str(sl_price),
                closePosition=True, reduceOnly=True,
            )
        if tp_price:
            r_tp = client.create_order(
                symbol=symbol,
                side=("SELL" if positionSide=="LONG" else "BUY"),
                positionSide=positionSide,
                type="TAKE_PROFIT_MARKET",
                stopPrice=str(tp_price),
                closePosition=True, reduceOnly=True,
            )

        resp = {"open": r_open, "sl": r_sl, "tp": r_tp}
        log_trade(data, resp)
        return jsonify({"ok": True, "result": resp})

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
