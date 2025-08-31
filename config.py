import os

SETTINGS = {
    "BINANCE_API_KEY": os.environ.get("BINANCE_API_KEY", "YOUR_TESTNET_KEY"),
    "BINANCE_API_SECRET": os.environ.get("BINANCE_API_SECRET", "YOUR_TESTNET_SECRET"),
    "BINANCE_UMF_BASE": os.environ.get("BINANCE_UMF_BASE", "https://testnet.binancefuture.com"),
    "WEBHOOK_SECRET": os.environ.get("WEBHOOK_SECRET", "CHANGE_ME_SECRET")
}
