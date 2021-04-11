import base64
import hashlib
import hmac
from http import HTTPStatus
from binascii import unhexlify
from typing import Dict
from quart import url_for
import urllib


def generate_bleskomat_lnurl_hash(secret: str):
    m = hashlib.sha256()
    m.update(f"{secret}".encode())
    return m.hexdigest()


def generate_bleskomat_lnurl_signature(
    payload: str, api_key_secret: str, api_key_encoding: str = "hex"
):
    if api_key_encoding == "hex":
        key = unhexlify(api_key_secret)
    elif api_key_encoding == "base64":
        key = base64.b64decode(api_key_secret)
    else:
        key = bytes(f"{api_key_secret}")
    return hmac.new(key=key, msg=payload.encode(), digestmod=hashlib.sha256).hexdigest()


def generate_bleskomat_lnurl_secret(api_key_id: str, signature: str):
    # The secret is not randomly generated by the server.
    # Instead it is the hash of the API key ID and signature concatenated together.
    m = hashlib.sha256()
    m.update(f"{api_key_id}-{signature}".encode())
    return m.hexdigest()


def get_callback_url():
    return url_for("bleskomat.api_bleskomat_lnurl", _external=True)


def is_supported_lnurl_subprotocol(tag: str) -> bool:
    return tag == "withdrawRequest"


class LnurlHttpError(Exception):
    def __init__(
        self,
        message: str = "",
        http_status: HTTPStatus = HTTPStatus.INTERNAL_SERVER_ERROR,
    ):
        self.message = message
        self.http_status = http_status
        super().__init__(self.message)


class LnurlValidationError(Exception):
    pass


def prepare_lnurl_params(tag: str, query: Dict[str, str]):
    params = {}
    if not is_supported_lnurl_subprotocol(tag):
        raise LnurlValidationError(f'Unsupported subprotocol: "{tag}"')
    if tag == "withdrawRequest":
        params["minWithdrawable"] = float(query["minWithdrawable"])
        params["maxWithdrawable"] = float(query["maxWithdrawable"])
        params["defaultDescription"] = query["defaultDescription"]
        if not params["minWithdrawable"] > 0:
            raise LnurlValidationError('"minWithdrawable" must be greater than zero')
        if not params["maxWithdrawable"] >= params["minWithdrawable"]:
            raise LnurlValidationError(
                '"maxWithdrawable" must be greater than or equal to "minWithdrawable"'
            )
    return params


encode_uri_component_safe_chars = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.!~*'()"
)


def query_to_signing_payload(query: Dict[str, str]) -> str:
    # Sort the query by key, then stringify it to create the payload.
    sorted_keys = sorted(query.keys(), key=str.lower)
    payload = []
    for key in sorted_keys:
        if not key == "signature":
            encoded_key = urllib.parse.quote(key, safe=encode_uri_component_safe_chars)
            encoded_value = urllib.parse.quote(
                query[key], safe=encode_uri_component_safe_chars
            )
            payload.append(f"{encoded_key}={encoded_value}")
    return "&".join(payload)


unshorten_rules = {
    "query": {"n": "nonce", "s": "signature", "t": "tag"},
    "tags": {
        "c": "channelRequest",
        "l": "login",
        "p": "payRequest",
        "w": "withdrawRequest",
    },
    "params": {
        "channelRequest": {"pl": "localAmt", "pp": "pushAmt"},
        "login": {},
        "payRequest": {"pn": "minSendable", "px": "maxSendable", "pm": "metadata"},
        "withdrawRequest": {
            "pn": "minWithdrawable",
            "px": "maxWithdrawable",
            "pd": "defaultDescription",
        },
    },
}


def unshorten_lnurl_query(query: Dict[str, str]) -> Dict[str, str]:
    new_query = {}
    rules = unshorten_rules
    if "tag" in query:
        tag = query["tag"]
    elif "t" in query:
        tag = query["t"]
    else:
        raise LnurlValidationError('Missing required query parameter: "tag"')
    # Unshorten tag:
    if tag in rules["tags"]:
        long_tag = rules["tags"][tag]
        new_query["tag"] = long_tag
        tag = long_tag
    if not tag in rules["params"]:
        raise LnurlValidationError(f'Unknown tag: "{tag}"')
    for key in query:
        if key in rules["params"][tag]:
            short_param_key = key
            long_param_key = rules["params"][tag][short_param_key]
            if short_param_key in query:
                new_query[long_param_key] = query[short_param_key]
            else:
                new_query[long_param_key] = query[long_param_key]
        elif key in rules["query"]:
            # Unshorten general keys:
            short_key = key
            long_key = rules["query"][short_key]
            if not long_key in new_query:
                if short_key in query:
                    new_query[long_key] = query[short_key]
                else:
                    new_query[long_key] = query[long_key]
        else:
            # Keep unknown key/value pairs unchanged:
            new_query[key] = query[key]
    return new_query
