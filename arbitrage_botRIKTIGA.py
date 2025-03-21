from web3 import Web3
import json
import requests
from pycoingecko import CoinGeckoAPI

# 1. Anslut till Ethereum-nätverket
infura_url = "https://mainnet.infura.io/v3/5cd30ab00e804164818b63870a8ac383"  # Ändra till din Infura URL
web3 = Web3(Web3.HTTPProvider(infura_url))

if web3.is_connected():
    print("Ansluten till Ethereum-nätverket")
else:
    print("Kunde inte ansluta till Ethereum-nätverket")
    exit()

# 2. Din wallets privata nyckel och adress
private_key = "78961fcd91badac2437998f2dc18e9dee64dc8182538b98c63f412af8f5f739a"  # OBS! Förvara aldrig din privata nyckel offentligt
wallet_address = web3.to_checksum_address("0xd5277bdda1F14a9c2FDa4a1e914995397B3D6DE0")

# 3. Ladda ABI och kontraktsadress
with open('abi.json', 'r') as abi_file:
    abi = json.load(abi_file)

contract_address = web3.to_checksum_address("0x82c40e6da7258EDb0cBdc6Adba52CB54E8BF9B4f")
contract = web3.eth.contract(address=contract_address, abi=abi)

# ERC20 ABI för att läsa WETH-saldo
erc20_abi = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    }
]

# Kontrollera saldon
def check_balances():
    try:
        eth_balance = web3.eth.get_balance(contract_address)
        print(f"Kontraktets ETH-saldo: {web3.from_wei(eth_balance, 'ether')} ETH")

        weth_address = web3.to_checksum_address("0xC02aaa39b223FE8D0a0E5C4F27eAD9083C756Cc2")  # WETH-kontraktet
        weth = web3.eth.contract(address=weth_address, abi=erc20_abi)  # Använd ERC20 ABI
        weth_balance = weth.functions.balanceOf(contract_address).call()
        print(f"Kontraktets WETH-saldo: {web3.from_wei(weth_balance, 'ether')} WETH")
    except Exception as e:
        print(f"Ett fel uppstod vid kontroll av saldon: {e}")

# Hämta pris från CoinGecko (ERC20 token på Uniswap/SushiSwap)
def get_price_from_coingecko(token_address):
    cg = CoinGeckoAPI()
    
    # Hämta CoinGecko ID för tokenen (se https://www.coingecko.com/en/api/documentation för referens)
    token_id = 'ethereum'  # Exempel för ETH, byt ut med motsvarande för andra tokens
    try:
        data = cg.get_price(ids=token_id, vs_currencies='usd')
        price = data[token_id]['usd']  # Hämta priset i USD
        return price
    except Exception as e:
        print(f"Ett fel uppstod vid hämtning av pris från CoinGecko: {e}")
        return 0.0

# Kontrollera om arbitrage är lönsamt
def check_arbitrage_profitability(token_address, gas_price_gwei, gas_limit, min_profit_threshold=0.05):
    price = get_price_from_coingecko(token_address)
    
    # Exempel på skillnad som vi kan jämföra (anpassa logik efter behov)
    price_difference = price  # Här kan du lägga till din logik för att jämföra två marknader
    
    # Beräkna gasavgift
    gas_cost = gas_price_gwei * gas_limit * 10**-9  # i ETH

    # Logga detaljerad information om pris och gasavgift
    print(f"Pris från CoinGecko: {price}")
    print(f"Beräknad gasavgift: {gas_cost} ETH")
    print(f"Pris skillnad: {price_difference}")
    
    # Tvinga arbitrage endast när vinsten är minst 100 gånger större än gasavgiften
    if price_difference - gas_cost > min_profit_threshold * 100:
        print(f"Arbitrage är lönsamt! Pris skillnad: {price_difference}, Gasavgift: {gas_cost}")
        return True
    else:
        print(f"Arbitrage inte lönsamt. Pris skillnad: {price_difference}, Gasavgift: {gas_cost}")
        return False

# Funktion för att exekvera arbitrage
def execute_arbitrage(amount_in_eth):
    try:
        nonce = web3.eth.get_transaction_count(wallet_address)

        # Skapa transaktion
        transaction = contract.functions.executeArbitrage(
            web3.to_wei(amount_in_eth, "ether")
        ).build_transaction({
            'chainId': 1,  # Mainnet
            'gas': 1000000,  # Gasgräns
            'gasPrice': web3.to_wei('20', 'gwei'),  # Gaspris
            'nonce': nonce
        })

        # Signera transaktion
        signed_txn = web3.eth.account.sign_transaction(transaction, private_key)

        # Skriv ut alla attribut för signed_txn
        print(dir(signed_txn))  # Lägg till denna rad här

        # Skicka transaktion
        tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)  # Försök igen med rawTransaction
        print(f"Transaktion skickad med hash: {web3.to_hex(tx_hash)}")
    except Exception as e:
        print(f"Ett fel uppstod vid exekvering av arbitrage: {e}")

# Ange beloppet för arbitrage, exempelvis 0.01 ETH
amount_in_eth = 0.01

# Kör programmet
if __name__ == "__main__":
    # Kontrollera om arbitrage är lönsamt innan du exekverar
    token_address = "0xYourTokenAddress"  # Byt ut med tokenadress
    gas_price_gwei = 30  # exempel på gaspris
    gas_limit = 1000000  # exempel på gasgräns

    if check_arbitrage_profitability(token_address, gas_price_gwei, gas_limit):
        check_balances()  # Den här raden ska nu fungera
        execute_arbitrage(amount_in_eth)
    else:
        print("Arbitrage inte lönsamt just nu.")
