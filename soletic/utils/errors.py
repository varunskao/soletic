from typing import Optional, Callable, Any
from solana.exceptions import SolanaRpcException


class InvalidProgramAddress(TypeError):

    def __init__(self, message):
        super().__init__(message)
        self.status_code = 400


class InvalidProgramSyntax(SyntaxError):

    def __init__(self, message):
        super().__init__(message)
        self.status_code = 400


class ProgramStateNotSupported(NotImplementedError):

    def __init__(self, message):
        super().__init__(message)
        self.status_code = 415


class HeliusAPIError(Exception):

    code_to_msg = {
        401: "Unauthorized. Invalid API key or restricted access due to Access Control Rules.",
        429: "Too Many Requests. Exceeded Rate Limits.",
        500: "Internal Server Error. Contact Helius support for assistance",
        503: "Service Unavailable. Server is temporarily overloaded or under maintenance.",
        504: "Gateway Timeout",
    }

    def __init__(self, message, status_code):
        super().__init__(message)
        self.status_code = status_code
        self.error_message = self.code_to_msg.get(status_code, "Unknown Error Code")
