# Import necessary libraries and modules
# pip install MetaTrader5
# pip install pandas
import MetaTrader5 as mt
import pandas as pd
from datetime import datetime
import time
from KEYS import *

# Define a class for the trading bot
class TraderBot:
    def __init__(self):
        # Initialize the TraderBot instance and set initial values
        self.login()  # Log in to MetaTrader5
        self.has_bought = False  # Track if a purchase has been made

    def login(self):
        # Log in to MetaTrader5 using the provided credentials
        try:
            mt.initialize()
            mt.login(username, password, server) # broker username password domain server
        except Exception as e:
            pass  # Handle login exceptions

    def market_order(self, symbol, volume, order_type,plus, **kwargs):
        # Place a market order based on specified parameters
        tick = mt.symbol_info_tick(symbol)
        spread = tick.ask - tick.bid # ASK-BID

        # Ensure buy order is placed only once
        if not self.has_bought and order_type == 'buy' and self.get_exposure('BTCUSD.i')>0:
            take_profit = tick.ask + plus
            request = {
                "action": mt.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": mt.ORDER_TYPE_BUY,
                "price": tick.ask,
                "sl": tick.ask - spread * 0.1,  # Properly consider spread for slippage
                "tp": take_profit,
                "deviation": 20,
                "magic": 100,
                "comment": "python market order",
                "type_time": mt.ORDER_TIME_GTC,
                "type_filling": mt.ORDER_FILLING_IOC,
            }

            # Uncomment the line below to send the order
            mt.order_send(request)
            self.has_bought = True  # Update the flag after the first purchase

        # Ensure sell limit order is placed only when there's an open position and the signal is sell
        positions = mt.positions_get(symbol=symbol)
        if positions and order_type == 'sell':
            position = positions[0]  # Assuming only one position is open
            sell_limit_price = tick.bid - spread * 0.1  # Properly consider spread for slippage
            sell_limit_request = {
                "action": mt.TRADE_ACTION_PENDING,
                "symbol": symbol,
                "volume": volume,
                "type": mt.ORDER_SELL_LIMIT,
                "price": sell_limit_price,
                "sl": position.sl,
                "tp": position.tp,
                "deviation": 20,
                "magic": 100,
                "comment": "python sell limit order",
                "type_time": mt.ORDER_TIME_GTC,
                "type_filling": mt.ORDER_FILLING_IOC,
            }

            # Uncomment the line below to send the sell limit order
            
            mt.order_send(sell_limit_request)
            #self.has_bought=False

    def get_exposure(self, symbol): # risk should be more than 0
        # Retrieve the exposure (total volume) for a given symbol
        positions = mt.positions_get(symbol=symbol)
        if positions:
            pos_df = pd.DataFrame(positions, columns=positions[0]._asdict().keys())
            exposure = pos_df['volume'].sum()
            return exposure
        return 0

    def signal(self, symbol, timeframe, sma_period): 
        # Generate a trading signal based on Simple Moving Average (SMA)
        bars = mt.copy_rates_from_pos(symbol, timeframe, 1, sma_period)
        bars_df = pd.DataFrame(bars)
        last_close = bars_df.iloc[-1].close
        sma = bars_df.close.mean()
        direction = 'flat'
        if last_close > sma:
            direction = 'buy'
        elif last_close < sma:
            direction = 'sell'
        return direction

# Main execution block
if __name__ == '__main__':
    # Instantiate the TraderBot
    tbot = TraderBot()
    SYMBOL = "BTCUSD.i"
    VOLUME = 0.1  # Updated volume to 0.1 can be changed by user
    TIMEFRAME = mt.TIMEFRAME_M1
    SMA_PERIOD = 10
    print("BOT is working ...\n")

    while True:
        # Retrieve symbol information, exposure, and trading signal
        symbol_info = mt.symbol_info(SYMBOL)
        exposure = tbot.get_exposure(SYMBOL)
        direction = tbot.signal(SYMBOL, TIMEFRAME, SMA_PERIOD)
        plus=5 # 5$ profit
        # Check for trading direction and place market order if conditions are met
        tbot.market_order(SYMBOL, VOLUME, direction,plus=plus)

        # Display relevant information
        print(tbot.has_bought)
        print('Time:', datetime.now())
        print('Symbol:', SYMBOL)
        print('Spread:', symbol_info.spread)
        print('Exposure:', exposure)
        print('Signal Direction:', direction)
        print('\n\n')
        time.sleep(5)  # Pause execution for 5 seconds
