import pytest
from brownie import Lottery, accounts, config, network, exceptions
from web3 import Web3

from scripts.deploy_lottery import deploy_lottery
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    get_account,
    fund_with_link,
    get_contract,
)


def test_get_entrance_fee():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    entrance_fee = lottery.getEntranceFee()

    assert entrance_fee == Web3.toWei(0.025, "ether")


def test_cant_enter_unless_started():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()

    with pytest.raises(exceptions.VirtualMachineError):
        lottery.enter(
            {"from": get_account(), "value": lottery.getEntranceFee() + 100000000}
        )


def test_can_start_and_enter_lottery():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee() + 100000000})

    assert lottery.players(0) == account


def test_can_end_lottery():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee() + 100000000})
    fund_with_link(lottery.address)
    lottery.endLottery({"from": account})

    assert lottery.lottery_state() == 2


def test_can_pick_winner_correctly():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    lottery.enter({"from": get_account(index=1), "value": lottery.getEntranceFee()})
    lottery.enter({"from": get_account(index=2), "value": lottery.getEntranceFee()})
    fund_with_link(lottery.address)

    transaction = lottery.endLottery({"from": account})
    request_id = transaction.events["RequestedRandomness"]["requestId"]
    STATIC_RNG = 777
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, STATIC_RNG, lottery.address, {"from": account}
    )
    starting_balance_of_account = account.balance()
    balance_of_lottery = lottery.balance()
    assert lottery.recentWinner() == account
    assert lottery.balance() == 0
    assert account.balance() == starting_balance_of_account + balance_of_lottery
