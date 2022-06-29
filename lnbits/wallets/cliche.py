import asyncio
import base64
import json
import urllib.parse
from os import getenv
from typing import AsyncGenerator, Dict, Optional

import httpx
from websockets import connect, serve
from websockets.exceptions import (
    ConnectionClosed,
    ConnectionClosedError,
    ConnectionClosedOK,
)

from .base import (
    InvoiceResponse,
    PaymentResponse,
    PaymentStatus,
    StatusResponse,
    Wallet,
)

async def echo(websocket):
    async for message in websocket:
        await websocket.send(message)

class ClicheWallet(Exception):
    pass


class UnknownError(Exception):
    pass


class ClicheWallet(Wallet):
    def __init__(self):
        url = getenv("CLICHE_URL")
        port = getenv("CLICHE_PORT")
        self.url = url[:-1] if url.endswith("/") else url

        self.ws_url = f"ws://{urllib.parse.urlsplit(self.url).netloc}:{port}"
        with serve(echo, f"ws://{self.url}", port):
            asyncio.Future()  # run forever
        

    async def status(self) -> StatusResponse:
        ws.send("get-info")
        result =  ws.recv()
        try:
            data = result.json()
        except:
            return StatusResponse(
                f"Failed to connect to {self.url}, got: '{r.text[:200]}...'", 0
            )

        if r.is_error:
            return StatusResponse(data["error"], 0)

        return StatusResponse(None, 1 * 1000)

    async def create_invoice(
        self,
        amount: int,
        memo: Optional[str] = None,
        description_hash: Optional[bytes] = None,
    ) -> InvoiceResponse:
        

        data: Dict = {"amountMsat": amount * 1000}
        description = ""
        if description_hash:
            description = description_hash.hex()
        else:
            description = memo or ""
        ws.send(f"create-invoice --msatoshi { amount * 1000 } --description { description }")
        result =  ws.recv()
        if result.is_error:
            try:
                data = result.json()
                error_message = data["error"]
            except:
                error_message = result.text
                pass

            return InvoiceResponse(False, None, None, error_message)

        data = result.json()
        return InvoiceResponse(True, data["paymentHash"], data["serialized"], None)

    async def pay_invoice(self, bolt11: str, fee_limit_msat: int) -> PaymentResponse:
        ws.send(f"pay-invoice --invoice { bolt11 }")
        result =  ws.recv()

        if "error" in result.json():
            try:
                data = result.json()
                error_message = data["error"]
            except:
                error_message = result.text
                pass
            return PaymentResponse(False, None, 0, None, error_message)

        data = result.json()

        checking_id = data[1]["params"]["payment_hash"]
        preimage = data[1]["params"]["preimage"]

        ws.send(f"check-payment --hash { data.payment_hash }")
        result =  ws.recv()

        if "error" in result.json():
            try:
                data = result.json()
                error_message = data["error"]
            except:
                error_message = result.text
                pass
            return PaymentResponse(
                True, checking_id, 0, preimage, error_message
            )  ## ?? is this ok ??

        data = result.json()
        fees = [i["status"] for i in data]
        fee_msat = sum([i["feesPaid"] for i in fees])

        return PaymentResponse(True, checking_id, fee_msat, preimage, None)

    async def get_invoice_status(self, checking_id: str) -> PaymentStatus:
        ws.send(f"check-payment --hash { checking_id }")
        result =  ws.recv()

        if result.is_error or "error" in data:
            return PaymentStatus(None)

        if data["method"] != "payment_received":
            return PaymentStatus(False)

        return PaymentStatus(True)

    async def get_payment_status(self, checking_id: str) -> PaymentStatus:
        ws.send(f"check-payment --hash { checking_id }")
        result =  ws.recv()

        if result.is_error:
            return PaymentStatus(None)

        if data["result"]["sent"] != True:
            return PaymentStatus(False)

        return PaymentStatus(True)

    async def paid_invoices_stream(self) -> AsyncGenerator[str, None]:

        try:
            async with connect(
                self.ws_url
            ) as ws:
                while True:
                    message = await ws.recv()
                    message = json.loads(message)

                    if message and message["payment_received"] or message["payment_succeeded"] or message["payment_failed"]:
                        yield message["payment_hash"]

        except (
            OSError,
            ConnectionClosedOK,
            ConnectionClosedError,
            ConnectionClosed,
        ) as ose:
            print("OSE", ose)
            pass

            print("lost connection to Cliche's websocket, retrying in 5 seconds")
            await asyncio.sleep(5)
