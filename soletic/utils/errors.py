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

    def __init__(self, message, status_code):
        super().__init__(message)
        self.status_code = status_code