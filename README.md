# Wix Home Assignment

## Overview
This repository contains my submission for the **Wix Data Engineer Home Assignment**, covering API integration, data modeling, and architectural design. The project includes:

1. **API Integration & Data Pipeline** - Extracting, transforming, and loading financial data from multiple APIs.
2. **Marketing Data Modeling** - Designing a robust data warehouse model for multi-platform marketing data.
3. **Architectural Design** - Building a scalable, real-time data architecture for event tracking.

## Setup Instructions
### **Prerequisites**
To run this project, ensure you have the following installed:
- **Python 3.10+**
- **MySQL 8.0+**
- Required Python packages (install using `pip`)

### **Running the ETL Pipeline**
1. Configure API and database credentials in `config.json` and `DB_Params.json`.
2. Run the ETL process:
   ```bash
   python ETL_stock.py
   ```
3. Check MySQL to verify that the data has been loaded correctly.

---

## Approach & Implementation
### **1. API Integration & Data Pipeline**
- Extracted stock price data from **Polygon.io API**.
- Fetched currency exchange rates from **Frankfurter API**.
- Designed an ETL pipeline that cleans, normalizes, and loads data into MySQL.
- Implemented **stored procedures** for efficient data handling.

### **2. Marketing Data Modeling**
- Designed a **dimensional model** to support multi-platform marketing analytics.
- Created **fact and dimension tables** optimized for querying and reporting.

### **3. Architectural Design**
- Design a **scalable event tracking system** using AWS services.


## Repository Structure
```
├── Section 1 - API Integration and Data Pipeline.md
    ├── ETL_stock.py
    ├── sql_connection.py
    ├── config.json
    ├── DB_Params.json
    ├── README.md
├── Section 2 - Marketing Data Modeling Challenge.md
    ├── marketing_data_modeling.md
├── Section 3 - Architectural Design Challenge.md
    ├── architectural_marketing_design.md
```