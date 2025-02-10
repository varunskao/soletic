from solders.pubkey import Pubkey
from solana.constants import BPF_LOADER_PROGRAM_ID

bpf_legacy_1 = Pubkey.from_string("BPFLoader1111111111111111111111111111111111")
bpf_legacy_2 = Pubkey.from_string("BPFLoader2111111111111111111111111111111111")
legacy_bpf_loaders = [bpf_legacy_1, bpf_legacy_2]

CHECK_PREFIX = "CHECK"
LOGIC_PREFIX = "LOGIC"
construct_prefix = lambda label, name: f"{label} - {name} |"
