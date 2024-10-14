import logging
import pandas as pd

def execute(date, position, price, unit):
    logging.info(f"Date: {date}, Position: {position}, Price: {price}, Unit: {unit}")
    trade_record = pd.Series(dtype=object)
    trade_record['Trade Date'] = date
    trade_record['Position'] = position
    trade_record['Fill Price'] = price
    trade_record['Unit'] = unit
    return trade_record.to_frame().T
    # Backtest.trades.append()

# Check if position is valid Open Long/Short when no open position
def check_open_position(trades):
    try:
        last_trade = trades[-1].loc[0, 'Position']
    except:
        last_trade = None

    if last_trade == 'Open Long' or last_trade == 'Open Short':
        status = True
    else:
        status = False

    return status

def check_position(trades, position):
    try:
        last_trade = trades[-1].loc[0, 'Position']
    except Exception as e:
        pass

    if position == 'Open Long' or position == 'Open Short':
        try:
            if len(trades) == 0 or (last_trade != 'Open Long' and last_trade != 'Open Short'):
                status = True
            else:
                status = False
        except:
            status = False
    elif position == 'Close Long':
        try:
            if (len(trades) > 0 and last_trade == 'Open Long'):
                status = True
            else:
                status = False
        except:
            status = False
    elif position == 'Close Short':
        try:
            if (len(trades) > 0 and last_trade == 'Open Short'):
                status = True
            else:
                status = False
        except:
            status = False
    else:
        status = False
    return status
    
def position_sizing(account_equity, account_usage, atr_b1, price):
    # unit = account_equity * account_usage / atr_b1
    # price = price
    # # make sure unit is not more than account equity
    # if unit * price > account_equity:
    #     unit = account_equity / price



    # No position sizing, use all account equity
    unit = account_equity / price

    # Sanity Check: 0 unit traded if account equity is less than 0
    if account_equity <= 0:
        unit = 0
    return unit

def stop_loss(trades, position, breakout_df):
    try:
        if position == 'Close Long':
            stop_loss = breakout_df.loc[trades[-1].loc[0, 'Trade Date'], 'long_stop_loss']
        elif position == 'Close Short':
            stop_loss = breakout_df.loc[trades[-1].loc[0, 'Trade Date'], 'short_stop_loss']
    except:
        stop_loss = 0
    return stop_loss