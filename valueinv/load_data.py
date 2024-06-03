import pandas as pd
import requests

def split_reports(data):
    annual_reports = []
    quarterly_reports = []
    for report in data['annualReports']:
        annual_reports.append(report)

    for report in data['quarterlyReports']:
        quarterly_reports.append(report)
    return annual_reports, quarterly_reports

def create_dataframe(annual_reports, quaterly_reports):
    df_list = []

    for report in annual_reports:
        df= pd.DataFrame(report,index=[0])
        df['ReportType'] ='Annual'
        df_list.append(df)

    for report in quaterly_reports:
        df= pd.DataFrame(report,index=[0])
        df['ReportType'] ='Quarterly'
        df_list.append(df)

    result_df = pd.concat(df_list,ignore_index=True)
    return result_df

def get_data(ticker,api_key):
    url_overview = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={api_key}'
    url_balance_sheet = f'https://www.alphavantage.co/query?function=BALANCE_SHEET&symbol={ticker}&apikey={api_key}'
    url_cashflow= f'https://www.alphavantage.co/query?function=CASH_FLOW&symbol={ticker}&apikey={api_key}'
    url_income_statement = f'https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol={ticker}&apikey={api_key}'

    data_overview = requests.get(url_overview, verify=False).json()
    data_balance_sheet = requests.get(url_balance_sheet, verify=False).json()
    data_cashflow = requests.get(url_cashflow, verify=False).json()
    data_income_statement = requests.get(url_income_statement, verify=False).json()

    overview = pd.DataFrame(data_overview, index=[0])

    annual_reports, quarterly_reports = split_reports(data_balance_sheet)
    balance = create_dataframe(annual_reports, quarterly_reports)

    annual_reports, quarterly_reports = split_reports(data_cashflow)
    cashflow = create_dataframe(annual_reports, quarterly_reports)

    annual_reports, quarterly_reports = split_reports(data_income_statement)
    income = create_dataframe(annual_reports, quarterly_reports)

    return overview,balance,cashflow,income



def get_data_csv(csv_files):
    dataframes = {}
    for csv_filename in csv_files:
        dataframe_name = csv_filename.split('.')[0]
        dataframe = pd.read_csv(csv_filename)

        dataframes[dataframe_name] =dataframe
    return dataframes

