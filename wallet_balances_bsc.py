# class AbstractContract is a template for any
# EVM based contract and initializing with contract address and ABI.
# Address and ABI can be found on blockchain explorer sush as https://etherscan.io

from abc import ABC
from web3 import Web3
import argparse
import requests
import json

# Binance Smart Chain http node provider
BSC = 'https://bsc-dataseed1.binance.org:443'


class ProviderInitException(Exception):
    pass


class AbstractContract(ABC):
    provider = None

    def __init__(self, address: str, ABI: str):

        if self.provider is not None:
            w3 = Web3(Web3.HTTPProvider(self.provider))
        else:
            raise ProviderInitException("Provider is wrong!")

        try:
            self.contract = w3.eth.contract(address, abi=ABI)
        except Exception as e:
            print(f'{e} in contract {address}')

    @property
    def address(self):
        return self.contract.address

    @property
    def abi(self):
        return self.contract.abi

    def get_functions_list(self) -> list:
        return self.contract.all_functions()


class BSCContract(AbstractContract):
    provider = BSC

    def __init__(self, address: str, ABI: str, wallet: str):
        self.wallet_address = wallet
        super().__init__(address, ABI)

    def get_decimals(self) -> int:
        return self.contract.functions.decimals().call()

    def get_balance(self) -> int:
        decimals = self.get_decimals()
        balance = self.contract.functions.balanceOf(self.wallet_address).call()
        return balance / 10**(len(str(balance)) - decimals)


def main_loop(wallet_address, contract_address):
    url_eth = "https://api.bscscan.com/api"

    # getting ABI by request
    API_ENDPOINT = url_eth + "?module=contract&action=getabi&address=" + str(contract_address)
    r = requests.get(url=API_ENDPOINT)
    ABI = r.json()["result"]
    ABI = json.loads(ABI)

    # creating contract
    my_contract = BSCContract(contract_address, ABI, wallet_address)

    # abi of balanceOf
    balanceOf_string = '{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}'
    balanceOf_list = json.loads(balanceOf_string)

    # abi of balanceOf
    decimals_string = '{"constant": true,"inputs": [],"name": "decimals","outputs": [{"name": "","type": "uint8"}],"type": "function"}'
    decimals_list = json.loads(decimals_string)

    # adding a balanceOf function if it doesn't exist in ABI
    if not my_contract.contract.find_functions_by_name('balanceOf'):
        ABI.append(balanceOf_list)
        my_contract = BSCContract(contract_address, ABI, wallet_address)

    # adding a decimals function if it doesn't exist in ABI
    if not my_contract.contract.find_functions_by_name('decimals'):
        ABI.append(decimals_list)
        my_contract = BSCContract(contract_address, ABI, wallet_address)

    return my_contract.get_balance()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-w", "--wallet", dest="wallet", required=True)
    parser.add_argument("-t", "--token", dest="token", required=True)
    args = parser.parse_args()
    result = main_loop(args.wallet, args.token)
    print("Output:", result)
