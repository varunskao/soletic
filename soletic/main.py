from typing import Dict, Generator, List
from datetime import datetime
import logging
import os
import asyncio

from solana.rpc.api import Client
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.signature import Signature
from solders.rpc.responses import GetSignaturesForAddressResp, GetAccountInfoResp
from solana.rpc.commitment import Finalized

from soletic.utils.constants import *
from soletic.utils.errors import *


logger = logging.getLogger(__name__)

async def get_last_n_signatures(client: AsyncClient, pubkey: Pubkey, limit: int = 1000, n: int=100) -> Generator[Signature, None, None]:
    """
    Recursively fetches signatures for the given address until the earliest transaction
    is found. In the process, it builds a queue of the latest signatures.
    """
    function_name = get_last_n_signatures.__name__
    log_prefix = construct_prefix(LOGIC_PREFIX, function_name)
    logger.info(f"{log_prefix} Start")

    last_n_signatures = iter([])
    earliest_signature = None

    while True:
        signatures: GetSignaturesForAddressResp = await client.get_signatures_for_address(
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

    return last_n_signatures

async def race_signature_fetch(client: AsyncClient, program_pubkeys: List[Pubkey]) -> Generator[Signature, None, None]:
    """Race between fetching signatures from program and program data accounts"""
    # Create tasks for both signature fetches
    tasks = [asyncio.create_task(get_last_n_signatures(client, pubkey)) for pubkey in program_pubkeys]
    
    # Wait for first task to complete or both to fail
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    
    # Cancel pending task
    for task in pending:
        task.cancel()
        
    # Get result from completed task
    completed_task = done.pop()
    try:
        signatures = await completed_task
        return signatures if signatures else iter([])
    except Exception as e:
        logger.error(f"Error fetching signatures: {e}")
        return iter([])

def get_n_earliest_signatures(
    client: Client, pubkey: Pubkey, limit: int = 1000, n: int=100
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

    while True:
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

def _get_async_client(context: Dict[str, str]) -> AsyncClient:
    url = f"https://{context.get("network")}.helius-rpc.com/"
    return AsyncClient(url, extra_headers={"Authorization": f"Bearer {os.getenv('HELIUS_API_KEY')}"})

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


async def _check_and_get_program_account(client: AsyncClient, program_pubkey: Pubkey) -> GetAccountInfoResp:
    """
    Validate that the provided program address is a valid program address 
    """
    func_name = _check_and_get_program_account.__name__
    log_prefix = construct_prefix(CHECK_PREFIX, func_name)
    logger.info(f"{log_prefix} Start Check")

    # Check whether we can retrieve the program account info
    try:
        program_account: GetAccountInfoResp = await client.get_account_info(program_pubkey)

        if not program_account.value:
            err_msg = f"'{program_pubkey}' does not exist. Please provide a valid program address."
            logger.error(f"{log_prefix} {err_msg}")
            raise InvalidProgramAddress(err_msg)

        if not program_account.value.executable:
            # Error out if the account is not a program account
            err_msg = f"'{program_pubkey}' is not a program account. Please provide a valid program address."
            logger.error(f"{log_prefix} {err_msg}")
            raise InvalidProgramAddress(err_msg)

    except Exception as e:
        err_msg = f"{log_prefix} Unable to retrieve account info. Issue: {e}."
        raise e

    return program_account


async def get_deployment_timestamp(
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
        client = _get_async_client(context)
        program_account = await _check_and_get_program_account(client, program_pubkey)

        # ---- LOGIC ----
        # If the program is upgradeable, check if the address corresponds to a program account or a program data account
        if program_account.value.owner == BPF_LOADER_PROGRAM_ID:
            program_bytes = bytes(program_account.value.data)
            is_program_account = program_bytes[0] == 2
            is_program_data_account = program_bytes[0] == 3

            if is_program_account:
                # If it is the program account, then get signatures from program data contract as it likely contains fewer signatures
                program_data_pubkey = Pubkey(program_bytes[4:36])
                # Fetch signatures in parallel until one returns signatures earlier than the other
                signatures = await race_signature_fetch(client=client, program_pubkeys=[program_pubkey, program_data_pubkey])
                transaction_block_time = find_first_valid_block_time_from_signatures(signatures)
                # signatures = get_n_earliest_signatures(client=client, pubkey=program_data_pubkey)

                # if not signatures:
                #     signatures = get_n_earliest_signatures(client=client, pubkey=program_pubkey)

                # transaction_block_time = find_first_valid_block_time_from_signatures(signatures)
            elif is_program_data_account:
                signatures = await get_last_n_signatures(client=client, pubkey=program_pubkey)
                transaction_block_time = find_first_valid_block_time_from_signatures(signatures)
            else:
                raise ProgramStateNotSupported("Buffer and Unitialized program states are not supported by this API")
        else:   
            # If the program is not upgradeable, then warn the user that performance will be degraded
            logger.warning("EXPECT DEGRADED PERFORMANCE - program account uses legacy BFP Loader")
            signatures = await get_last_n_signatures(client=client, pubkey=program_pubkey)
            transaction_block_time = find_first_valid_block_time_from_signatures(signatures)

        return transaction_block_time

    except Exception as e:
        code = getattr(e, "code", "UNDEFINED")
        return f"{code} | {e.args[0].__str__()}" 