from pyteal import *
from algosdk.v2client import algod
from algosdk import account, mnemonic, transaction
from algosdk.transaction import ApplicationCreateTxn, wait_for_confirmation
from algosdk.logic import get_application_address
import base64

# Ticket Manager Smart Contract for Solution AI on Algorand
# This contract manages ticket creation, storage of hashes, and NFT issuance

def approval_program():
    # Global state keys
    ticket_count_key = Bytes("ticket_count")
    total_supply_key = Bytes("total_supply")

    # On creation - initialize global state
    on_creation = Seq([
        App.globalPut(ticket_count_key, Int(0)),
        App.globalPut(total_supply_key, Int(21000000000000)),  # 21 trillion
        Return(Int(1))
    ])

    # Create ticket - store hash and increment count
    create_ticket = Seq([
        App.globalPut(ticket_count_key, App.globalGet(ticket_count_key) + Int(1)),
        # Store ticket hash in global state (simplified - in practice use box storage)
        App.globalPut(Concat(Bytes("ticket_"), Itob(App.globalGet(ticket_count_key))), Txn.application_args[1]),
        Return(Int(1))
    ])

    # Issue NFT for premium ticket
    issue_nft = Seq([
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields({
            TxnField.type_enum: TxnType.AssetConfig,
            TxnField.config_asset_total: Int(1),
            TxnField.config_asset_decimals: Int(0),
            TxnField.config_asset_unit_name: Bytes("SOLAI-NFT"),
            TxnField.config_asset_name: Txn.application_args[1],  # Ticket title
            TxnField.config_asset_url: Txn.application_args[2],  # Metadata URL
            TxnField.config_asset_manager: Txn.sender(),
            TxnField.config_asset_reserve: Txn.sender(),
            TxnField.config_asset_freeze: Txn.sender(),
            TxnField.config_asset_clawback: Txn.sender(),
        }),
        InnerTxnBuilder.Submit(),
        Return(Int(1))
    ])

    # Transfer tokens (for rewards)
    transfer_tokens = Seq([
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields({
            TxnField.type_enum: TxnType.AssetTransfer,
            TxnField.xfer_asset: Btoi(Txn.application_args[1]),  # Asset ID
            TxnField.asset_amount: Btoi(Txn.application_args[2]),  # Amount
            TxnField.asset_receiver: Txn.accounts[1],  # Recipient
        }),
        InnerTxnBuilder.Submit(),
        Return(Int(1))
    ])

    # Main program logic
    program = Cond(
        [Txn.application_id() == Int(0), on_creation],
        [Txn.on_completion() == OnComplete.DeleteApplication, Return(Int(0))],
        [Txn.on_completion() == OnComplete.UpdateApplication, Return(Int(0))],
        [Txn.on_completion() == OnComplete.CloseOut, Return(Int(1))],
        [Txn.on_completion() == OnComplete.OptIn, Return(Int(1))],
        [Txn.application_args[0] == Bytes("create_ticket"), create_ticket],
        [Txn.application_args[0] == Bytes("issue_nft"), issue_nft],
        [Txn.application_args[0] == Bytes("transfer"), transfer_tokens],
    )

    return program

def clear_program():
    return Return(Int(1))

if __name__ == "__main__":
    with open("ticket_manager_approval.teal", "w") as f:
        f.write(compileTeal(approval_program(), Mode.Application, version=5))

    with open("ticket_manager_clear.teal", "w") as f:
        f.write(compileTeal(clear_program(), Mode.Application, version=5))