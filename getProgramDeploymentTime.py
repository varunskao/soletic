import requests
from typing import Dict, Union
import os
import logging
from solana.rpc.api import Client 
from solders.pubkey import Pubkey
from solders.signature import Signature
from solders.rpc.responses import GetSignaturesForAddressResp, GetTransactionResp
from solana.rpc.commitment import Finalized
from collections import deque
import asyncio


logger = logging.getLogger(__name__)

# Define the RPC endpoint (this example uses mainnet-beta)
rpc_url = lambda network: f"https://{network}.helius-rpc.com/"


def get_program_accounts(context: Dict[str, str], address: str):
    """
    Calls the getProgramAccounts endpoint.
    """
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getProgramAccounts",
        "params": [address]
    }
    url = rpc_url(context.get("network")) + f"?api-key={os.getenv("HELIUS_API_KEY")}"
    response = requests.post(url, json=payload)
    # TODO: Add better error handling here and logging for verbosity
    response.raise_for_status()  # Raises an exception for HTTP errors
    data = response.json()
    return data, data.get("result", [])


def get_earliest_signatures(context: Dict[str, str], address: Pubkey, limit: int=1000) -> deque:
    """
    Recursively fetches signatures for the given address until the earliest transaction
    is found, all the while building a queue of size 2000 of the latest signatures.
    """
    client = _get_client(context)
    before: Union[Signature, None] = None
    signature_queue = deque(maxlen=2000)

    while True:
        signatures: GetSignaturesForAddressResp = client.get_signatures_for_address(
            account=address, 
            limit=limit, 
            before=before, 
            commitment=Finalized
        )
        if not signatures.value:
            # No further signatures returned; exit loop.
            logger.warning(f"signatures response: {signatures}") 
            break

        signature_queue.extend(signatures.value)

        # If we received less than the limit, this batch is the final one.
        if len(signatures.value) < limit:
            break

        # Otherwise, set the "before" parameter for the next call.
        before = signatures.value[-1]

    return signature_queue


def get_transaction(context: Dict[str, str], signature: str):
    """
    Fetches detailed transaction information using the getTransaction endpoint.
    Here we request the parsed JSON format to simplify inspection of the instructions.
    """
    client = _get_client(context)
    txn = client.get_transaction(tx_sig=signature, commitment="finalize", max_supported_transaction_version=0)
    return txn


def is_deployment_transaction(tx_info, program_address):
    """
    Heuristically determine whether the given transaction represents
    the deployment of the program by inspecting its instructions.

    The idea is to check for an instruction that comes from a known program loader.
    For example, a deployment transaction typically involves either:
      - The legacy BPF Loader ("BPFLoader1111111111111111111111111111111111"), or
      - The upgradeable loader ("BPFLoaderUpgradeab1e11111111111111111111111")
    and the instruction should reference the program account.

    This function may need to be customized based on the deployment patterns.
    """
    try:
        message = tx_info["transaction"]["message"]
        instructions = message["instructions"]
    except KeyError:
        return False

    # Define known loader program IDs.
    KNOWN_LOADERS = {
        "BPFLoader1111111111111111111111111111111111",
        "BPFLoaderUpgradeab1e11111111111111111111111"
    }

    for ix in instructions:
        # In the parsed JSON format, each instruction might include a "program" field.
        if "program" in ix:
            if ix["program"] in KNOWN_LOADERS:
                # Check if the program account is referenced among the instruction's accounts.
                accounts = ix.get("accounts", [])
                if program_address in accounts:
                    # Optionally, if available, check for a parsed instruction type such as "finalize" or "deploy".
                    if "parsed" in ix and isinstance(ix["parsed"], dict):
                        if ix["parsed"].get("type") in {"finalize", "deploy"}:
                            return True
                    else:
                        # If no extra detail is available, assume this instruction qualifies.
                        return True
        # Fallback in case instructions are not using the "program" key.
        elif "programId" in ix:
            if ix["programId"] in KNOWN_LOADERS:
                accounts = ix.get("accounts", [])
                if program_address in accounts:
                    return True
    return False


async def find_deployment_transaction(context, program_address: str) -> int:
    """
    Retrieves the last num_transactions for the program account and
    iterates over them (in chronological order) to identify the transaction
    that corresponds to the program deployment.
    """

    EXPECTED_ACCOUNT_KEYS = []
    client = _get_client(context)
    signature_queue = get_earliest_signatures(context, program_address)

    async def process_signature(signature):
        tx: GetTransactionResp = await client.get_transaction(signature)
        # TODO: Need to handle case when the transaction object is empty
        if (
            len(tx.value.transaction.transaction.signatures) == 2 and
            tx.value.transaction.transaction.account_keys[-4:] == EXPECTED_ACCOUNT_KEYS and  # You'll need to define this
            not tx.meta.err and
            any(f"Deployed program {program_address}" in log for log in tx.value.transaction.meta.log_messages)
        ):
            return tx.block_time
        return None

    tasks = [process_signature(sig) for sig in signature_queue]
   
    try:
        for future in asyncio.as_completed(tasks):
            result = await future
            if result:
                # Cancel remaining tasks
                for task in tasks:
                    task.cancel()
                signature_queue.clear()
                return result
                
        raise Exception("No deployment transaction found")
        
    except Exception as e:
        # Cancel all tasks on error
        for task in tasks:
            task.cancel()
        raise e


def _get_client(context):
    url = rpc_url(context.get("network")) + f"?api-key={os.getenv("HELIUS_API_KEY")}"
    return Client(url)


def _validate_program_address(program_address: str):
    try:
        program_pubkey = Pubkey.from_string(program_address)
    except ValueError as ve:
        err_msg = f"Program address: {program_address} is invalid because {ve}"
        logger.error(err_msg)
        return err_msg
    
    client = _get_client(context)

    # Check whether we can retrieve the program account info
    # TODO: Need to centralize error handling from the client.
    try:
        program_account_info = client.get_account_info(program_pubkey)
    except Exception as e:
        err_msg = f"Unable to retrieve account info. Issue: {e}"
        logger.error(err_msg)
        return err_msg
    
    # Make sure the address provided corresponds to a program address
    if not program_account_info.value:
        err_msg = f"Address: {program_address}, does not exist. Please provide a valid program address."
        return err_msg
    elif not program_account_info.value.executable:
        err_msg = f"Address: {program_address}, is not marked as executable. Please provide a valid program address."
        return err_msg


def get_deployment_timestamp(context: Dict[str, str], program_address: str, num_transactions: int=50):
    """
    Determines the deployment timestamp by first finding the deployment
    transaction among the last num_transactions and then extracting its blockTime.
    """

    err_msg = _validate_program_address(program_address)
    if err_msg: return err_msg

    tx_info = find_deployment_transaction(context, program_address)
    if not tx_info:
        print("Could not find a deployment transaction among the last {} transactions.".format(num_transactions))
        return None

    # The transaction's "slot" is available; check if blockTime is included.
    slot = tx_info.get("slot")
    if slot is None:
        print("Slot information missing in the transaction.")
        return None

    block_time_tx = tx_info.get("blockTime")
    if block_time_tx is not None:
        return block_time_tx
    else:
        # Fallback: use getBlockTime endpoint if blockTime is not present.
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getBlockTime",
            "params": [slot]
        }
        url = rpc_url(context.get("network")) + f"?api-key={os.getenv("HELIUS_API_KEY")}"
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        return data.get("result", None)


if __name__ == "__main__":
    context = {"network": "mainnet"}
    to_pubkey = lambda a:  Pubkey.from_string(a)
    token_address = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
    jupiter_v4_address = "JUP4Fb2cqiRUcaTHdrPC8h2gNsA2ETXiPDD33WcGuJB"
    jupiter_v6_address = "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4"

    # ------- Signatures for Address -------
    # sigs = get_signatures_for_address(context, jupiter_v4_address)
    # print(f"sigs len: {len(sigs)}")
    # print(f"sigs: {sigs}")

    # ------- Earliest Signatures for Address -------
    # earliest_signature, last_20_signatures = get_earliest_signature(context, jupiter_v6_address)
    # print(f"earliest_signature: {earliest_signature}")
    # print(f"last_20_signatures: {last_20_signatures}")
  
    # ------- Accounts for Program -------
    data, program_accounts = get_program_accounts(context, jupiter_v6_address)
    print(f"program_accounts: {program_accounts}")
    print(f"data: {data}")