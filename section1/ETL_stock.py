import pandas as pd
import requests
import json
import os
from sql_connection import sql_alchemy

class StockETL:
    def __init__(self, config_path="./config.json"):
        """
        Initialize the StockETL class, load stock and currency exchange data, and set up database connection.
        """
        self.config_path = config_path
        self.load_config()
        self.db = sql_alchemy("stock_data_warehouse")

    def load_config(self):
        """
        Load configuration file containing API parameters and target currency.
        """
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found at {self.config_path}")

        with open(self.config_path, 'r') as file:
            self.config = json.load(file)

        self.frankfurter_currency_data = self.config["Frankfurter_Currency"]
        self.polygon_stock_data = self.config["Polygon_Stock_Data"]
        self.target_currency = self.config["target_currency"]

    def get_exchange_rates(self):
        """
        Fetch exchange rates from the Frankfurter API for a base currency and target currencies.
        Return - Dictionary containing the exchange rates for the target currencies.
        """
        base_url = "https://api.frankfurter.dev/v1/"
        trade_date = self.frankfurter_currency_data.get("trade_date", None)
        base_currency = self.frankfurter_currency_data.get("base_currency", None)
        target_currencies = self.frankfurter_currency_data.get("target_currencies", [])

        if not all([trade_date, base_currency]):
            raise ValueError("Both 'trade_date' and 'base_currency' are required.")

        url = os.path.join(base_url, f"{trade_date}?base={base_currency}")
        if target_currencies:
            url += "&symbols=" + ",".join(target_currencies)

        response = requests.get(url)

        if response.status_code == 200:
            return response.json().get('rates', {})
        else:
            raise Exception(f"Error fetching exchange rates: {response.status_code} - {response.text}")

    def get_stock_data(self):
        """
        Fetch stock data from Polygon.io for a given ticker and date range.
        Return - List of dictionaries containing stock data.
        """
        base_url = "https://api.polygon.io"
        ticker = self.polygon_stock_data.get("ticker", None)
        start_date = self.polygon_stock_data.get("start_date", None)
        end_date = self.polygon_stock_data.get("end_date", None)
        multiplier = self.polygon_stock_data.get("multiplier", 1)
        timespan = self.polygon_stock_data.get("timespan", 'day')
        api_key = self.polygon_stock_data.get("api_key", None)

        if not all([ticker, start_date, end_date, api_key]):
            raise ValueError("Parameters 'ticker', 'start_date', 'end_date', and 'api_key' are required.")

        endpoint = f"/v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{start_date}/{end_date}"
        url = f"{base_url}{endpoint}?apiKey={api_key}"

        response = requests.get(url)

        if response.status_code == 200:
            return response.json().get('results', [])
        else:
            raise Exception(f"Error fetching stock data: {response.status_code} - {response.text}")

    def clean_stock_data(self, stock_data):
        """
        Clean and normalize stock data.
        Return - Cleaned and normalized DataFrame.
        """
        df = pd.DataFrame(stock_data)

        required_columns = {'t', 'o', 'h', 'l', 'c', 'v'}   # Check for required columns
        if not required_columns.issubset(df.columns):
            raise ValueError(f"Missing required columns: {required_columns - set(df.columns)}")

        df.rename(columns={
                            't': 'timestamp',
                            'o': 'open',
                            'h': 'high',
                            'l': 'low',
                            'c': 'close',
                            'v': 'volume'}, inplace=True)

        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')                # Convert timestamp to readable format
        df.dropna(inplace=True)
        df = df[(df[['open', 'high', 'low', 'close', 'volume']] >= 0).all(axis=1)]  # Filter out unrealistic values (e.g., negative prices)

        return df

    def convert_stock_prices(self, stock_df, exchange_rates):
        """
        Convert stock prices to the target currency.
        """
        if self.target_currency not in exchange_rates:
            raise ValueError(f"Exchange rate for {self.target_currency} not available.")

        stock_df['currency'] = self.target_currency
        stock_df['exchange_rate'] = exchange_rates[self.target_currency]

        for col in ['open', 'high', 'low', 'close']:    
            stock_df[col] *= stock_df['exchange_rate']

        return stock_df

    def insert_currency_data(self, currency_code):
        """
        Insert currency into the database.
        """
        self.db.call_sp("insert_currency", (currency_code,))
        self.db._commit()

    def insert_stock_data(self):
        """
        Insert stock into the database and return its ID.
        """
        stock_id = self.db.call_sp_with_output("insert_stock", (self.polygon_stock_data["ticker"],))
        self.db._commit()
        return stock_id

    def insert_exchange_rates(self, exchange_rates):
        """
        Insert exchange rates into the database.
        """
        for target_currency, rate in exchange_rates.items():
            self.db.call_sp("insert_exchange_rate", (
                self.frankfurter_currency_data["trade_date"],
                self.frankfurter_currency_data["base_currency"],
                target_currency,
                rate
            ))
        self.db._commit()

    def insert_stock_prices(self, stock_id, df_stock_prices):
        """
        Insert stock price data into the database.
        """
        for _, row in df_stock_prices.iterrows():
            self.db.call_sp("insert_stock_price", (stock_id, row["timestamp"].date(), row["currency"], row["exchange_rate"], 
                                                    row["open"], row["high"], row["low"], row["close"], row["volume"]))
        self.db._commit()

    def run_etl(self):
        """
        Run the pipeline: fetch data, process, and insert into the database.
        """
        try:
            exchange_rates = self.get_exchange_rates()
            stock_data = self.get_stock_data()

            cleaned_stock_df = self.clean_stock_data(stock_data)
            converted_stock_df = self.convert_stock_prices(cleaned_stock_df, exchange_rates)

            for code in exchange_rates.keys():
                self.insert_currency_data(code)

            self.insert_exchange_rates(exchange_rates)
            stock_id = self.insert_stock_data()
            self.insert_stock_prices(stock_id, converted_stock_df)

        except Exception as e:
            print(f"ETL process failed: {e}")
            exit("Error inserting data into the database.")

if __name__ == "__main__":
    etl = StockETL()
    etl.run_etl()

# to run
# to add docstring
# to write readme

# check if the base curency like target
# if target not in the list of the upload, good? to think..