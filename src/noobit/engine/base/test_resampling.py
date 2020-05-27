import pandas as pd

from noobit_user import get_abs_path


user_path = get_abs_path()
file_path = f"{user_path}/data/kraken_xbt-usd_historical_trade_data.csv"
test_file_path = f"{user_path}/data/test_resampling.csv"


def write_100_lines_to_test_file():


    try:
        df = pd.read_csv(file_path,
                        #  names=[
                            #  "symbol",
                            #  "side",
                            #  "ordType",
                            #  "avgPx",
                            #  "cumQty",
                            #  "grossTradeAmt",
                            #  "transactTime",
                        #  ],
                            names=["price", "volume", "time", "side", "type", "misc"],
                            index_col=2,
                            parse_dates=True
                            #  header=None,
                            #  skiprows=1
                            )
        df = df.iloc[1:100]
        df.index = pd.to_datetime(df.index, unit="s")
        print(df.head(5))
        print(df.tail(5))
        df.to_csv(path_or_buf=f"{user_path}/data/test_resampling.csv",
                mode="w",
                header=False,
                index=True
                )
    except FileNotFoundError:
        print("CSV File not does exist, run historical trades aggregator")
    except Exception as e:
        raise e


def read_in_test_file():

    df = pd.read_csv(test_file_path,
                     names=["time", "price", "volume", "side", "type", "misc"],
                     index_col=0,
                     parse_dates=True,
                    #  date_parser=lambda x: pd.to_datetime(x, unit="s")
                     #  header=None,
                     #  skiprows=1
                     )
    return df


def resample(df):
    resampled_df = df.resample('1H').agg({'price': 'ohlc', 'volume': 'sum'})  #! change later to avgPx and cumQty
    return resampled_df





if __name__ == "__main__":
    # write_100_lines_to_test_file()
    df = read_in_test_file()
    resampled = resample(df)
    resampled = resampled.droplevel(0, axis=1)
    print(resampled.head(5))
    print(resampled.tail(5))