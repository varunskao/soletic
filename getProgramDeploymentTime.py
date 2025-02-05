import requests
from typing import Dict
import os

# Define the RPC endpoint (this example uses mainnet-beta)
rpc_url = lambda network: f"https://api.{network}.solana.com/"

def get_signatures_for_address(context: Dict[str, str], address: str, limit: int=1000, before=None):
    """
    Calls the getSignaturesForAddress endpoint with an optional "before" parameter.
    """
    params = {"limit": limit}
    if before:
        params["before"] = before

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getSignaturesForAddress",
        "params": [address, params]
    }
    url = rpc_url(context.get("network")) + f"?api-key={os.getenv("HELIUS_API_KEY")}"
    response = requests.post(url, json=payload)
    # TODO: Add better error handling here and logging for verbosity
    response.raise_for_status()  # Raises an exception for HTTP errors
    data = response.json()
    return data.get("result", [])

def get_last_n_signatures(context: Dict[str, str], address: str, n: int=50):
    """
    Retrieves the most recent n signatures for the address.
    Note: The RPC returns the most recent signatures first, so we reverse
    the list to iterate in chronological order.
    """
    sigs = get_signatures_for_address(context, address, limit=n)
    if sigs:
        return list(reversed(sigs))
    return []

def get_transaction(context: Dict[str, str], signature: str):
    """
    Fetches detailed transaction information using the getTransaction endpoint.
    Here we request the parsed JSON format to simplify inspection of the instructions.
    """
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTransaction",
        "params": [signature, "jsonParsed"]
    }
    url = rpc_url(context.get("network")) + f"?api-key={os.getenv("HELIUS_API_KEY")}"
    response = requests.post(url, json=payload)
    response.raise_for_status()
    data = response.json()
    return data.get("result", {})

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

def find_deployment_transaction(context: Dict[str, str], program_address: str, num_transactions: int=50):
    """
    Retrieves the last num_transactions for the program account and
    iterates over them (in chronological order) to identify the transaction
    that corresponds to the program deployment.
    """
    signatures = get_last_n_signatures(context, program_address, n=num_transactions)
    if not signatures:
        print("No signatures found for address:", program_address)
        return None

    # Iterate from the oldest of the last num_transactions upward.
    for sig_obj in signatures:
        sig = sig_obj["signature"]
        tx_info = get_transaction(context, sig)
        if not tx_info:
            continue

        # Skip transactions that failed.
        meta = tx_info.get("meta", {})
        if meta.get("err") is not None:
            continue

        if is_deployment_transaction(tx_info, program_address):
            return tx_info

    return None

def get_deployment_timestamp(context: Dict[str, str], program_address: str, num_transactions: int=50):
    """
    Determines the deployment timestamp by first finding the deployment
    transaction among the last num_transactions and then extracting its blockTime.
    """
    tx_info = find_deployment_transaction(context, program_address, num_transactions=num_transactions)
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