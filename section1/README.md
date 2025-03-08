# Section 1 - API Integration and Data Pipeline

## Overview

This project is an ETL (Extract, Transform, Load) pipeline designed to fetch stock market data from the **Polygon.io API** and currency exchange rates from the **Frankfurter API**. The data is transformed, stored in a **MySQL database**, and enables analysis of stock prices across different currencies.

## Project Structure

### The project consists of the following files:

1. **`config.json`** - Contains configuration settings for API requests, including:
   - **Frankfurter Currency Exchange API** parameters: base currency, target currencies, trade date.
   - **Polygon Stock API** parameters: stock ticker, date range, API key.
   - Target currency for stock price conversion.

2. **`DB_Params.json`** - Defines database connection parameters:
   - Database name
   - User credentials
   - Connection port

3. **`ETL_stock.py`** - The core script responsible for:
   - Fetching exchange rates from the **Frankfurter API**.
   - Fetching stock data from the **Polygon.io API**.
   - Cleaning and normalizing stock data.
   - Converting stock prices to the target currency.
   - Inserting transformed data into the database using stored procedures.
   - Executing the **ETL process** from extraction to loading.

4. **`sql_connection.py`** - Handles MySQL database connection using SQLAlchemy:
   - Establishing a connection to MySQL.
   - Calling stored procedures.
   - Managing transactions and commits.


## Running the ETL Process
To execute the ETL process, run the following command:
```bash
python ETL_stock.py
```

## Code Explanation

### `ETL_stock.py`
The `StockETL` class contains:

1. **`__init__(self, config_path='./config.json')`**
   - Loads the configuration file.
   - Initializes the database connection.

2. **`load_config(self)`**
   - Reads API parameters from `config.json`.
   - Stores them as class attributes.

3. **`get_exchange_rates(self)`**
   - Calls the **Frankfurter API** to retrieve currency exchange rates.
   - Returns exchange rates as a dictionary.

4. **`get_stock_data(self)`**
   - Calls the **Polygon.io API** to retrieve stock data.
   - Returns a list of stock price records.

5. **`clean_stock_data(self, stock_data)`**
   - Converts raw stock data into a structured DataFrame.
   - Renames columns for clarity.
   - Converts timestamps to readable datetime format.
   - Removes missing and invalid values.

6. **`convert_stock_prices(self, stock_df, exchange_rates)`**
   - Converts stock prices to the configured target currency.
   - Adds exchange rate and currency information to the DataFrame.

7. **`insert_currency_data(self, currency_code)`**
   - Inserts currency codes into the database.

8. **`insert_stock_data(self)`**
   - Inserts stock metadata (ticker) into the database.
   - Returns the stock ID.

9. **`insert_exchange_rates(self, exchange_rates)`**
   - Inserts exchange rates into the database.

10. **`insert_stock_prices(self, stock_id, df_stock_prices)`**
    - Inserts stock prices into the database.

11. **`run_etl(self)`**
    - Orchestrates the entire ETL process.

--- 

### `sql_connection.py`
This script manages MySQL connections and execution of stored procedures:

1. **`__init__(self, db)`**
   - Reads database credentials from `DB_Params.json`.
   - Establishes a MySQL connection using **SQLAlchemy**.

2. **`call_sp(self, sp_name, data)`**
   - Executes stored procedures without output parameters.

3. **`call_sp_with_output(self, sp_name, data, outParam='p_stock_id')`**
   - Executes stored procedures with output parameters.

4. **`__sp_get_params(self, sp_name)`**
   - Retrieves stored procedure parameters dynamically.

5. **`_commit(self)`**
   - Commits transactions to the database.



## MySQL Database Schema

1. User Setup:
    ``` sql
    CREATE USER 'etl_stock'@'%' identified by '123456';
    GRANT RELOAD, SUPER, PROCESS ON *.* TO 'etl_stock'@'%';
    FLUSH privileges;
    ``` 

2. Database Creation
    ``` sql
    CREATE SCHEMA stock_data_warehouse DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_ci;
    GRANT ALL PRIVILEGES ON stock_data_warehouse.* TO 'etl_stock'@'%';
    FLUSH PRIVILEGES;
    GRANT SELECT, INSERT, UPDATE, DELETE ON stock_data_warehouse.* TO 'etl_stock'@'%';
    FLUSH PRIVILEGES;
    ``` 

3. Tables:
*  `currency` - Stores available currency codes.
    ``` sql
    CREATE TABLE currency (
        currency_code VARCHAR(5) PRIMARY KEY);
    ``` 

* `stock` - Stores stock metadata.
    ``` sql
    CREATE TABLE stock (
        stock_id INT PRIMARY KEY AUTO_INCREMENT,
        ticker VARCHAR(10) UNIQUE NOT NULL
    );
    ```

* `stock_prices` - Stores daily stock prices with currency conversion.
    ``` sql
    CREATE TABLE stock_prices (
        stock_id INT NOT NULL,
        trade_date DATE NOT NULL,
        currency_code VARCHAR(3) NOT NULL,
        exchange_rate DECIMAL(10,6) NOT NULL,
        open_price DECIMAL(15,4),
        high_price DECIMAL(15,4),
        low_price DECIMAL(15,4),
        close_price DECIMAL(15,4),
        volume BIGINT,
        PRIMARY KEY (stock_id, trade_date, currency_code),
        FOREIGN KEY (stock_id) REFERENCES stock(stock_id),
        FOREIGN KEY (currency_code) REFERENCES currency(currency_code)
    );
    ```

* `exchange_rates` - Stores exchange rates between currencies on a given trade date.
    ``` sql
    CREATE TABLE exchange_rates (
        trade_date DATE NOT NULL,
        base_currency VARCHAR(5) NOT NULL,
        target_currency VARCHAR(5) NOT NULL,
        exchange_rate DECIMAL(10,6) NOT NULL,
        PRIMARY KEY (trade_date, base_currency, target_currency),
        FOREIGN KEY (base_currency) REFERENCES currency(currency_code),
        FOREIGN KEY (target_currency) REFERENCES currency(currency_code)
    );
    ```

4. Stored Procedures:

* `insert_currency`
    ``` sql
    CREATE PROCEDURE insert_currency( IN p_currency_code VARCHAR(5))
    BEGIN
        INSERT INTO currency (currency_code)
        VALUES (p_currency_code)
        ON DUPLICATE KEY UPDATE currency_code = p_currency_code;
    END;
    ```

* `insert_stock`:
    ``` sql
    CREATE PROCEDURE insert_stock(
        IN p_ticker VARCHAR(10),
        OUT p_stock_id INT)
    BEGIN
        INSERT INTO stock (ticker)
        VALUES (p_ticker)
        ON DUPLICATE KEY UPDATE ticker = p_ticker;

        SELECT stock_id INTO p_stock_id FROM stock WHERE ticker = p_ticker;
    END ;
    ```

* `insert_exchange_rate`:
    ``` sql
    CREATE PROCEDURE insert_exchange_rate(
        IN p_trade_date DATE,
        IN p_base_currency VARCHAR(5),
        IN p_target_currency VARCHAR(5),
        IN p_exchange_rate DECIMAL(10,6)
    )
    BEGIN
        INSERT INTO exchange_rates (trade_date, base_currency, target_currency, exchange_rate)
        VALUES (p_trade_date, p_base_currency, p_target_currency, p_exchange_rate)
        ON DUPLICATE KEY UPDATE trade_date = p_trade_date,
                                base_currency = p_base_currency,
                                target_currency = p_target_currency,
                                exchange_rate = p_exchange_rate;
    END;
    ```

* `insert_stock_price`:
    ``` sql
    CREATE PROCEDURE insert_stock_price(
        IN p_stock_id INT,
        IN p_trade_date DATE,
        IN p_currency_code VARCHAR(5),
        IN p_exchange_rate DECIMAL(10,6),
        IN p_open_price DECIMAL(15,4),
        IN p_high_price DECIMAL(15,4),
        IN p_low_price DECIMAL(15,4),
        IN p_close_price DECIMAL(15,4),
        IN p_volume BIGINT
    )
    BEGIN
        INSERT INTO stock_prices (stock_id, trade_date, currency_code, exchange_rate, open_price, high_price, low_price, close_price, volume)
        VALUES (p_stock_id, p_trade_date, p_currency_code, p_exchange_rate, p_open_price, p_high_price, p_low_price, p_close_price, p_volume)
        ON DUPLICATE KEY UPDATE 
            open_price = p_open_price,
            high_price = p_high_price,
            low_price = p_low_price,
            close_price = p_close_price,
            volume = p_volume;
    END;
    ```


## Documentation explaining:

### Data Pipeline Architecture

The ETL pipeline follows these steps:
* **Extract**: Retrieves data from two APIs (Polygon.io for stock data, Frankfurter for exchange rates).
* **Transform**: Cleans and normalizes stock data, ensuring correct timestamp formats, column mappings, and currency conversion.
* **Load**: Stores transformed data into a structured MySQL database using stored procedures for efficient data insertion.

The architecture ensures that data flows seamlessly from APIs to the database while handling errors and ensuring data consistency.

### Data Modeling Approach

The database is designed to support efficient querying and analysis of stock price movements and currency conversion. The schema follows a dimensional modeling approach, with:
* Fact tables (stock_prices) storing transactional stock price data.
* Dimension tables (stock, currency, exchange_rates) providing reference information.

This structure allows easy historical analysis and efficient filtering based on different dimensions such as currency and stock ticker.

### How Currency-Converted Stock Analysis Works
* Exchange rates are fetched from the **Frankfurter API**.
* Stock prices are retrieved in the default base currency (USD) from **Polygon.io**.
* Using the exchange rates, stock prices are converted to the target currency before being stored in stock_prices.
* Analysts can query stock prices in any available currency using the exchange_rates table.

### Configuring the Pipeline for Different Stocks or Currencies
The config.json file allows users to specify:
* Stock ticker (ticker field under Polygon_Stock_Data).
* Time range for stock data (`start_date`, `end_date`).
* Target currency (`target_currency` field).
* Additional exchange rates by updating the Frankfurter_Currency section.

Modifying config.json and re-running the ETL process updates the database with new stock and currency data.

### Handling API Failures and Missing Data
The pipeline includes:
* Error handling: API responses are validated, and failures result in informative errors rather than crashing the process.
* Retries: If an API request fails due to temporary issues, the system can be extended to implement retry logic.
*  Missing data handling:
    * If stock data is missing for specific dates, the system skips invalid records.
    * If exchange rates are unavailable, stock prices remain in the base currency, allowing conversion at a later stage.

### Scheduling and Monitoring in Production
To run in production, the ETL process can be scheduled and monitored as follows:
* Scheduling:
    * Use cron jobs or Apache Airflow to automate the ETL process on a daily/hourly basis.
    * Define execution intervals based on business needs (e.g., daily stock updates).
* Monitoring:
    * Implement logging mechanisms to track API responses and database insertions.
    * Set up alerts (e.g., via email or Slack) for failures in data extraction or database operations.
    * Store logs in an external service such as AWS CloudWatch or ELK Stack for deeper analysis.


## Notes:

### Extending API 1: Polygon.io Stock API

* The current implementation uses the free/sample endpoints.
To enable authenticated access and retrieve a larger dataset, replace the API key with a valid authenticated API key.
Modify the API request headers to include authentication tokens.

* Adding Additional Data Fields
If we need to store additional stock-related data (such as country, industry, or sector), we can extend the stock table by adding new columns.
Similarly, for currency data, we can extend the currency table to include currency symbols, country names, and other relevant metadata.
