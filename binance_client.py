import time, hmac, hashlib, requests, urllib.parse

class BinanceUMFutures:
    def __init__(self, api_key: str, api_secret: str, base_url: str):
        self.api_key = api_key
        self.api_secret = api_secret.encode()
        self.base_url = base_url.rstrip("/")

    def _ts(self): return int(time.time() * 1000)
    def _sign(self, query: str): return hmac.new(self.api_secret, query.encode(), hashlib.sha256).hexdigest()
    def _headers(self): return {"X-MBX-APIKEY": self.api_key}

    def _request(self, method: str, path: str, params: dict=None, signed: bool=False):
        url = f"{self.base_url}{path}"
        params = params or {}
        if signed:
            params["timestamp"] = self._ts()
            query = urllib.parse.urlencode(params, doseq=True)
            params["signature"] = self._sign(query)
        if method=="GET": r=requests.get(url, params=params, headers=self._headers())
        elif method=="POST": r=requests.post(url, params=params, headers=self._headers())
        elif method=="DELETE": r=requests.delete(url, params=params, headers=self._headers())
        else: raise ValueError("Unsupported method")
        if r.status_code >= 400: raise Exception(f"{r.status_code} {r.text}")
        return r.json()

    def set_position_mode(self, dualSide=True):
        return self._request("POST","/fapi/v1/positionSide/dual",{"dualSidePosition": "true" if dualSide else "false"},signed=True)
    def set_leverage(self, symbol:str, leverage:int):
        return self._request("POST","/fapi/v1/leverage",{"symbol":symbol,"leverage":leverage},signed=True)
    def set_margin_type(self, symbol:str, marginType="CROSSED"):
        return self._request("POST","/fapi/v1/marginType",{"symbol":symbol,"marginType":marginType},signed=True)
    def create_order(self, **kwargs):
        return self._request("POST","/fapi/v1/order",kwargs,signed=True)
