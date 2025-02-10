from typing import Dict, Generator
import logging
import logging.handlers
import os
from pathlib import Path
import json
from functools import wraps
from solana.rpc.api import Client
from solders.pubkey import Pubkey
from solders.signature import Signature
from solders.rpc.responses import GetSignaturesForAddressResp, GetAccountInfoResp
from solana.rpc.commitment import Finalized
from solana.exceptions import SolanaRpcException
from httpx import HTTPStatusError

from soletic.utils.constants import *
from soletic.utils.errors import *


class SolanaProgramAnalyzer:
    def __init__(self, log_file: str, verbose: bool = False, debug: bool = False):
        """Initialize the analyzer with logging configuration."""
        self.log_file = log_file
        self.logger = self._setup_logger(verbose, debug)
        self._cache = self._load_cache()

    def _setup_logger(self, verbose: bool, debug: bool) -> logging.Logger:
        """Configure logging based on verbose flag and log file configuration."""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)

        # Create formatters
        console_formatter = logging.Formatter("%(message)s")
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Configure console handler based on verbose flag
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(console_formatter)

        if verbose:
            console_handler.setLevel(logging.INFO)
            logger.addHandler(console_handler)
        if debug:
            console_handler.setLevel(logging.DEBUG)
            logger.addHandler(console_handler)

        # Get absolute path and set up file handler
        file_path = os.path.join(os.path.expanduser("~"), self.log_file)
        file_handler = logging.handlers.RotatingFileHandler(
            file_path, maxBytes=10485760, backupCount=5  # 10MB
        )
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)

        return logger

    def _get_cache_file(self) -> Path:
        """Get cache file path from environment variable or default location"""
        cache_dir = os.path.join(
            os.path.expanduser("~"), os.getenv("SOLETIC_CACHE_DIR", ".soletic_cache")
        )
        Path(cache_dir).mkdir(parents=True, exist_ok=True)
        return Path(cache_dir) / "soletic_cache.json"

    def _load_cache(self) -> Dict:
        """Load the cache from file"""
        try:
            with open(self._get_cache_file()) as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.logger.debug("No existing cache file found or cache file corrupted")
            return {}

    def _save_cache(self):
        """Save the current cache to file"""
        try:
            with open(self._get_cache_file(), "w") as f:
                json.dump(self._cache, f)
        except Exception as e:
            self.logger.warning(f"Error saving to persistent cache: {e}")

    def _get_client(self, network: str) -> Client:
        """Create and return a Solana client"""
        function_name = "_get_client"
        log_prefix = construct_prefix(LOGIC_PREFIX, function_name)
        self.logger.debug(f"{log_prefix} Start Logic")

        try:
            url = f"https://{network}.helius-rpc.com/"
            client = Client(
                url,
                extra_headers={
                    "Authorization": f"Bearer {os.getenv('HELIUS_API_KEY')}"
                },
            )
            client.is_connected()
            return client
        except SolanaRpcException as e:
            original_exc = e.__cause__
            status_code = (
                original_exc.response.status_code
                if hasattr(original_exc, "response")
                else -1
            )
            error_message = HeliusAPIError.code_to_msg.get(
                status_code, "Unkonwn Status Code"
            )
            self.logger.error(f"{log_prefix} {error_message}")
            self.logger.error(f"{log_prefix} Traceback: {e.__traceback__}")
            raise HeliusAPIError(error_message, status_code=status_code)

    def _check_and_get_pubkey_from_address(self, program_address: str) -> Pubkey:
        """Validate that the provided program address is a valid pubkey"""
        function_name = "_check_and_get_pubkey_from_address"
        log_prefix = construct_prefix(CHECK_PREFIX, function_name)
        self.logger.debug(f"{log_prefix} Start Check")

        try:
            program_pubkey = Pubkey.from_string(program_address)
            self.logger.debug(
                f"{log_prefix} Provided program address ({program_address}) is a valid pubkey."
            )
            return program_pubkey
        except ValueError as e:
            err_msg = f"Program address: {program_address}, is invalid because: {e}."
            self.logger.error(f"{log_prefix} {err_msg}")
            raise InvalidProgramSyntax(err_msg)

    def _check_and_get_program_account(
        self, client: Client, program_pubkey: Pubkey
    ) -> GetAccountInfoResp:
        """Validate that the provided program address is a valid program address"""
        function_name = "_check_and_get_program_account"
        log_prefix = construct_prefix(CHECK_PREFIX, function_name)
        self.logger.debug(f"{log_prefix} Start Check")

        try:
            program_account: GetAccountInfoResp = client.get_account_info(
                program_pubkey
            )

            if not program_account.value:
                err_msg = f"'{program_pubkey}' does not exist. Please provide a valid program address."
                self.logger.error(f"{log_prefix} {err_msg}")
                raise InvalidProgramAddress(err_msg)

            if not program_account.value.executable:
                err_msg = f"'{program_pubkey}' is not a program account. Please provide a valid program address."
                self.logger.error(f"{log_prefix} {err_msg}")
                raise InvalidProgramAddress(err_msg)

            return program_account

        except SolanaRpcException as e:
            original_exc = e.__cause__
            status_code = (
                original_exc.response.status_code
                if hasattr(original_exc, "response")
                else -1
            )
            error_message = HeliusAPIError.code_to_msg.get(
                status_code, "Unkonwn Status Code"
            )
            self.logger.error(f"{log_prefix} {error_message}")
            self.logger.error(f"{log_prefix} Traceback: {e.__traceback__}")
            raise HeliusAPIError(error_message, status_code=status_code)
        except Exception as e:
            err_msg = f"Unable to retreive account info: {e}"
            self.logger.error(f"{log_prefix} {err_msg}")
            raise

    def get_last_n_signatures(
        self, client: Client, pubkey: Pubkey, limit: int = 1000, n: int = 100
    ) -> Generator[Signature, None, None]:
        """
        Recursively fetches signatures for the given address until the earliest transaction
        is found. In the process, it builds a queue of the latest signatures.
        """
        function_name = "get_last_n_signatures"
        log_prefix = construct_prefix(LOGIC_PREFIX, function_name)
        self.logger.info(f"{log_prefix} Start")

        last_n_signatures = iter([])
        earliest_signature = None

        try:
            while True:
                signatures: GetSignaturesForAddressResp = (
                    client.get_signatures_for_address(
                        account=pubkey,
                        limit=limit,
                        before=earliest_signature,
                        commitment=Finalized,
                    )
                )

                if not signatures.value:
                    self.logger.warning(f"signatures response: {signatures}")
                    break

                if len(signatures.value) < limit:
                    last_n_signatures = reversed(signatures.value[-n:])
                    break

                earliest_signature = signatures.value[-1].signature

            return last_n_signatures

        except SolanaRpcException as e:
            original_exc = e.__cause__
            status_code = (
                original_exc.response.status_code
                if hasattr(original_exc, "response")
                else -1
            )
            error_message = HeliusAPIError.code_to_msg.get(
                status_code, "Unkonwn Status Code"
            )
            self.logger.error(f"{log_prefix} {error_message}")
            self.logger.error(f"{log_prefix} Traceback: {e.__traceback__}")
            raise HeliusAPIError(error_message, status_code=status_code)
        except Exception as e:
            err_msg = f"Error fetching signatures: {e}"
            self.logger.error(f"{log_prefix} {err_msg}")
            raise

    @staticmethod
    def find_first_valid_block_time_from_signatures(
        signature_iter: Generator[Signature, None, None],
    ) -> int:
        """Find the earliest valid signature and return its block time"""
        return next(
            (
                signature.block_time
                for signature in signature_iter
                if signature and (not signature.err) and signature.block_time
            ),
            -1,
        )

    @staticmethod
    def parse_error(e: Exception) -> str:
        """Parse error messages consistently"""
        code = getattr(e, "status_code", "UNDEFINED")
        return f"{code} | {e.args[0].__str__()}"

    def get_deployment_timestamp(
        self, program_address: str, network: str, use_cache: bool = True
    ):
        """Determines the deployment timestamp of the given program address."""
        function_name = "get_deployment_timestamp"
        log_prefix = construct_prefix(LOGIC_PREFIX, function_name)
        self.logger.info(f"{log_prefix} Start Logic")

        if use_cache:
            cache_key = f"{program_address}_{network}"
            cached_res = self._cache.get(cache_key)
            if cached_res and not isinstance(cached_res, str):
                return self._cache[cache_key]

        client = None

        try:
            program_pubkey = self._check_and_get_pubkey_from_address(program_address)
            client = self._get_client(network)
            program_account = self._check_and_get_program_account(
                client, program_pubkey
            )

            if program_account.value.owner == BPF_LOADER_PROGRAM_ID:
                program_bytes = bytes(program_account.value.data)
                is_program_account = program_bytes[0] == 2
                is_program_data_account = program_bytes[0] == 3

                if is_program_account:
                    program_data_pubkey = Pubkey(program_bytes[4:36])
                    signatures = self.get_last_n_signatures(
                        client=client, pubkey=program_data_pubkey
                    )

                    if not signatures:
                        signatures = self.get_last_n_signatures(
                            client=client, pubkey=program_pubkey
                        )

                    transaction_block_time = (
                        self.find_first_valid_block_time_from_signatures(signatures)
                    )
                elif is_program_data_account:
                    signatures = self.get_last_n_signatures(
                        client=client, pubkey=program_pubkey
                    )
                    transaction_block_time = (
                        self.find_first_valid_block_time_from_signatures(signatures)
                    )
                else:
                    raise ProgramStateNotSupported(
                        "Buffer and Unitialized program states are not supported by this API"
                    )
            else:
                self.logger.warning(
                    "EXPECT DEGRADED PERFORMANCE - program account uses legacy BFP Loader"
                )
                signatures = self.get_last_n_signatures(
                    client=client, pubkey=program_pubkey
                )
                transaction_block_time = (
                    self.find_first_valid_block_time_from_signatures(signatures)
                )

            if use_cache and transaction_block_time != -1:
                self._cache[cache_key] = transaction_block_time
                self._save_cache()

            return transaction_block_time

        except HeliusAPIError as e:
            return self.parse_error(e)
        except SolanaRpcException as e:
            original_exc = e.__cause__
            status_code = (
                original_exc.response.status_code
                if hasattr(original_exc, "response")
                else -1
            )
            error_message = HeliusAPIError.code_to_msg.get(
                status_code, "Unkonwn Status Code"
            )
            self.logger.error(f"{log_prefix} {error_message}")
            self.logger.error(f"{log_prefix} Traceback: {e.__traceback__}")
            return self.parse_error(
                HeliusAPIError(error_message, status_code=status_code)
            )
        except Exception as e:
            return self.parse_error(e)
        finally:
            if client:
                client._provider.session.close()
