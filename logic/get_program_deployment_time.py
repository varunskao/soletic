from typing import Dict, Generator
from datetime import datetime
import logging
import os

from solana.rpc.api import Client
from solders.pubkey import Pubkey
from solders.signature import Signature
from solders.rpc.responses import GetSignaturesForAddressResp, GetAccountInfoResp
from solana.rpc.commitment import Finalized

from soletic.utils.constants import *
from soletic.utils.errors import *


logger = logging.getLogger(__name__)


def get_n_earliest_signatures(
    client: Client, pubkey: Pubkey, limit: int = 100, n: int=100
) -> Generator[Signature, None, None]:
    """
    Recursively fetches signatures for the given address until the earliest transaction
    is found. In the process, it builds a queue of the latest signatures.
    """
    function_name = get_n_earliest_signatures.__name__
    log_prefix = construct_prefix(LOGIC_PREFIX, function_name)
    logger.info(f"{log_prefix} Start")

    last_n_signatures = iter([])
    earliest_signature = None
    limit_multiplier = 1

    while True:
        # Linearly increase the limit of the response until max limit is reached
        limit *= limit_multiplier

        signatures: GetSignaturesForAddressResp = client.get_signatures_for_address(
            account=pubkey, limit=limit, before=earliest_signature, commitment=Finalized
        )

        if not signatures.value:
            # No further signatures returned; exit loop.
            logger.warning(f"signatures response: {signatures}")
            break

        # If we received less than the limit, this batch is the final one.
        if len(signatures.value) < limit:
            last_n_signatures = reversed(signatures.value[-n:])
            break

        earliest_signature = signatures.value[-1].signature
        limit_multiplier = min(limit_multiplier + 2, 10)

    return last_n_signatures


def find_first_valid_block_time_from_signatures(signature_iter: Generator[Signature, None, None]) -> int:
    """
    The function scans the signature_queue in reverse order (oldest to newest) to find the earliest valid signature and return its block time. 
    If no valid signature exists, it returns -1.
    """
    return next(
        (signature.block_time for signature in signature_iter if signature and (not signature.err) and signature.block_time),
        -1,
    )


def _get_client(context: Dict[str, str]) -> Client:
    url = f"https://{context.get("network")}.helius-rpc.com/"
    return Client(url, extra_headers={"Authorization": f"Bearer {os.getenv('HELIUS_API_KEY')}"})


def _check_and_get_pubkey_from_address(program_address: str) -> Pubkey:
    """
    Validate that the provided program address is a valid pubkey
    """
    function_name = _check_and_get_pubkey_from_address.__name__
    log_prefix = construct_prefix(CHECK_PREFIX, function_name)
    logger.info(f"{log_prefix} Start Check")

    try:
        program_pubkey = Pubkey.from_string(program_address)
        logger.info(f"{log_prefix} Provided program address ({program_address}) is a valid pubkey.")
        return program_pubkey
    except ValueError as e:
        err_msg = f"Program address: {program_address}, is invalid because: {e}."
        logger.error(f"{log_prefix} {err_msg}")
        raise InvalidProgramSyntax(err_msg)


def _check_and_get_program_account(client: Client, program_pubkey: Pubkey) -> GetAccountInfoResp:
    """
    Validate that the provided program address is a valid program address 
    """
    func_name = _check_and_get_program_account.__name__
    log_prefix = construct_prefix(CHECK_PREFIX, func_name)
    logger.info(f"{log_prefix} Start Check")

    # Check whether we can retrieve the program account info
    try:
        program_account: GetAccountInfoResp = client.get_account_info(program_pubkey)
    except Exception as e:
        err_msg = f"{log_prefix} Unable to retrieve account info. Issue: {e}."
        raise e

    if not program_account.value:
        err_msg = f"'{program_pubkey}' does not exist. Please provide a valid program address."
        logger.error(f"{log_prefix} {err_msg}")
        raise InvalidProgramAddress(err_msg)
    elif not program_account.value.executable:
        # Error out if the account is not a program account
        err_msg = f"'{program_pubkey}' is not a program account. Please provide a valid program address."
        logger.error(f"{log_prefix} {err_msg}")
        raise InvalidProgramAddress(err_msg)
    elif bytes(program_account.value.data)[0] not in [2, 3]:
        # Warn user if the account queried is not of the right account state
        logger.warning(f"{log_prefix} Program account: {program_pubkey} is either uninitialized (not fully setup) or is a buffer variant.")

    return program_account


def get_deployment_timestamp(
    context: Dict[str, str], 
    program_address: str, 
):
    """
    Determines the deployment timestamp of the given program address.
    """
    # TODO: Wrap in a big try-except and handle errors well

    func_name = get_deployment_timestamp.__name__
    log_prefix = construct_prefix(LOGIC_PREFIX, func_name)
    logger.info(f"{log_prefix} Start Logic")

    try:
        # ---- CHECK ----
        program_pubkey = _check_and_get_pubkey_from_address(program_address)
        client = _get_client(context)
        program_account = _check_and_get_program_account(client, program_pubkey)

        # ---- LOGIC ----
        # If the program is upgradeable, check if the address corresponds to a program account or a program data account
        if program_account.value.owner == BPF_LOADER_PROGRAM_ID:
            program_bytes = bytes(program_account.value.data)
            is_program_account = program_bytes[0] == 2
            is_program_data_account = program_bytes[0] == 3

            if is_program_account:
                # If it is the program account, then get signatures from program data contract as it likely contains fewer signatures
                program_data_pubkey = Pubkey(program_bytes[4:36])
                signatures = get_n_earliest_signatures(client=client, pubkey=program_data_pubkey)

                # Fall back in case the program data contract returns no signatures
                if not signatures:
                    signatures = get_n_earliest_signatures(client=client, pubkey=program_pubkey)

                transaction_block_time = find_first_valid_block_time_from_signatures(signatures)
            elif is_program_data_account:
                signatures = get_n_earliest_signatures(client=client, pubkey=program_pubkey)
                transaction_block_time = find_first_valid_block_time_from_signatures(signatures)
            else:
                raise ProgramStateNotSupported("Buffer and Unitialized program states are not supported by this API")
        else:   
            # If the program is not upgradeable, then warn the user that performance will be degraded
            logger.info("User requested deployment time of program account using legacy BFP Loader, expect performance degradation")
            signatures = get_n_earliest_signatures(client=client, pubkey=program_pubkey)
            transaction_block_time = find_first_valid_block_time_from_signatures(signatures)

        return transaction_block_time

    except Exception as e:
        code = getattr(e, "code", "UNDEFINED")
        return f"{code} | {e.args[0].__str__()}" 