import pandas as pd

import numpy as np
# import appdirs as ad
# ad.user_cache_dir = lambda *args: "/tmp"
import yfinance as yf

def convert_to_numeric(df, exception_columns):
    for column in df.columns:
        if column not in exception_columns:
            df[column] = pd.to_numeric(df[column], errors='coerce') / 1000000
    return df


def process_data(cashflow, income, balance, earnings):
    # Erstellen von Dataframes zur weiteren Verarbeitung
    def select_data(df, report_type, keep=None):
        selected_df = df[df['ReportType'] == report_type].copy()
        selected_df.drop_duplicates(subset=['fiscalDateEnding'], keep='first', inplace=True)
        if keep is None:
            return selected_df.reset_index(drop=True)
        else:
            cols_to_drop = [col for col in selected_df.columns if col not in keep]
            selected_df.drop(columns=cols_to_drop, inplace=True)
        # print(selected_df.columns)

        return selected_df.reset_index(drop=True)

    def finalise_dataframe(dfs, min_rows=None):
        if min_rows is not None:
            dfs_trimmed = [df.iloc[:min_rows] for df in dfs]
        else:
            dfs_trimmed = dfs

        concatenated_df = pd.concat(dfs_trimmed, axis=1)
        concatenated_df.drop(columns=['ReportType'], inplace=True)
        concatenated_df = concatenated_df.loc[:, ~concatenated_df.columns.duplicated()]
        concatenated_df = concatenated_df.fillna(0)

        return concatenated_df

    keep_cashflow = ['fiscalDateEnding', 'operatingCashflow',
                     'capitalExpenditures', 'dividendPayout', 'netIncome', 'ReportType']

    keep_balance = ['fiscalDateEnding', 'totalAssets', 'currentDebt','cashAndCashEquivalentsAtCarryingValue','totalCurrentAssets',
                    'inventory', 'currentNetReceivables', 'otherCurrentAssets', 'totalCurrentLiabilities',
                    'currentAccountsPayable', 'shortTermDebt', 'totalNonCurrentLiabilities', 'longTermDebtNoncurrent',
                    'longTermDebt', 'currentLongTermDebt', 'otherCurrentLiabilities', 'totalShareholderEquity',
                    'ReportType','cashAndShortTermInvestments',]

    keep_income = ['fiscalDateEnding', 'totalRevenue', 'ebit', 'netIncome', 'ReportType']

    cashflow_qu = select_data(cashflow, 'Quarterly',keep=keep_cashflow)
    balance_qu = select_data(balance, 'Quarterly',keep=keep_balance)
    income_qu = select_data(income, 'Quarterly',keep=keep_income)
    earnings_qu = select_data(earnings, 'Quarterly', keep=['fiscalDateEnding', 'reportedEPS'])

    cashflow_an = select_data(cashflow, 'Annual',keep=keep_cashflow)
    balance_an = select_data(balance, 'Annual',keep=keep_balance)
    income_an = select_data(income, 'Annual',keep=keep_income)
    earnings_an = select_data(earnings, 'Annual', keep=['fiscalDateEnding', 'reportedEPS'])

    income_an['fiscalDateEnding'] = pd.to_datetime(income_an['fiscalDateEnding'])
    income_qu['fiscalDateEnding'] = pd.to_datetime(income_qu['fiscalDateEnding'])
    income_an['Year_Month'] = income_an['fiscalDateEnding'].dt.to_period('M')
    income_qu['Year_Month'] = income_qu['fiscalDateEnding'].dt.to_period('M')
    
    earnings_an['fiscalDateEnding'] = pd.to_datetime(earnings_an['fiscalDateEnding'])
    earnings_qu['fiscalDateEnding'] = pd.to_datetime(earnings_qu['fiscalDateEnding'])
    earnings_an['Year_Month'] = earnings_an['fiscalDateEnding'].dt.to_period('M')
    earnings_qu['Year_Month'] = earnings_qu['fiscalDateEnding'].dt.to_period('M')
    earnings_an.drop(columns=['fiscalDateEnding'],inplace=True)
    earnings_qu.drop(columns=['fiscalDateEnding'],inplace=True)
    
    income_an = pd.merge(income_an, earnings_an, how='inner', on='Year_Month')
    income_qu = pd.merge(income_qu, earnings_qu, how='inner', on='Year_Month')
    
    income_an.drop(columns=['Year_Month'],inplace=True)
    income_qu.drop(columns=['Year_Month'],inplace=True)


    dfs_an = [cashflow_an, income_an, balance_an]
    dfs_qu = [cashflow_qu, income_qu]

    min_rows_an = min(len(df) for df in dfs_an)
    min_rows_qu = min(len(df) for df in dfs_qu)

    all_reports_an = finalise_dataframe(dfs_an, min_rows=min_rows_an)
    all_reports_qu = finalise_dataframe(dfs_qu, min_rows=min_rows_qu)

    return all_reports_an, all_reports_qu, balance_qu


def caculate_avg_price_by_year(all_reports_an,ticker):
    # Laden der Daten aus yF
    min_date_an = all_reports_an['fiscalDateEnding'].min()
    max_date = pd.Timestamp.today().strftime('%Y-%m-%d')
    data_an = yf.download(ticker, start=min_date_an, end=max_date).reset_index()
    data_an['Date'] = pd.to_datetime(data_an['Date'])
    data_an['year'] = data_an['Date'].dt.year

    # Berechnung avg_price
    all_reports_an['fiscalDateEnding'] = pd.to_datetime(all_reports_an['fiscalDateEnding'])
    all_reports_an['year'] = all_reports_an['fiscalDateEnding'].dt.year
    average_close_by_year = data_an.groupby('year')['Close'].mean().reset_index()
    average_close_by_year.columns = ['year', 'avg_Kurs']
    average_close_by_year['avg_Kurs'] = round(average_close_by_year['avg_Kurs'].astype(float), 2)

    # Merge Price mit Dataframe
    all_reports_an = pd.merge(all_reports_an, average_close_by_year, how='inner', on='year')
    all_reports_an.drop(columns=['fiscalDateEnding'], inplace=True)
    all_reports_an['year'] = all_reports_an['year'].astype(int)
    return all_reports_an,data_an


def create_ttm_dataframe(all_reports_qu, balance_qu,ticker):
    # Laden der Daten aus yF
    all_reports_qu = all_reports_qu.iloc[:4]
    min_date_qu = all_reports_qu['fiscalDateEnding'].min()
    max_date = pd.Timestamp.today().strftime('%Y-%m-%d')
    data_qu = yf.download(ticker, start=min_date_qu, end=max_date)

    # Berechnung avg_price
    average_close_by_ttm = data_qu.Close.mean()
    ttm = all_reports_qu.select_dtypes(include=['number']).sum(axis=0)
    ttm = pd.DataFrame(ttm).transpose()
    ttm['year'] = 'TTM'
    ttm['avg_Kurs'] = average_close_by_ttm
    # Merge Price mit Dataframe
    balance_ttm = balance_qu[balance_qu['fiscalDateEnding'] == balance_qu['fiscalDateEnding'].max()].drop(
        columns=['ReportType', 'fiscalDateEnding'])
    ttm = pd.concat([ttm, balance_ttm], axis=1)
    return ttm,data_qu


def calculate_metrics(all_reports):
    # Berechnung der neuen Spalten
    all_reports.loc[:, 'freeCashflow'] = all_reports['operatingCashflow'] - all_reports['capitalExpenditures']
    all_reports.loc[:, 'shares_dil'] = all_reports['netIncome'] / all_reports['reportedEPS']
    all_reports.loc[:, 'pershareRevenue'] = round(all_reports['totalRevenue'] / all_reports['shares_dil'], 2)
    all_reports.loc[:, 'pershareOperativerCashflow'] = round(
        all_reports['operatingCashflow'] / all_reports['shares_dil'], 2)
    all_reports.loc[:, 'pershareFreeCashflow'] = round(all_reports['freeCashflow'] / all_reports['shares_dil'], 2)
    all_reports.loc[:, 'pershareDividend'] = round(all_reports['dividendPayout'] / all_reports['shares_dil'], 2)
    all_reports.loc[:, 'persharebookvalue'] = round(all_reports['totalShareholderEquity'] / all_reports['shares_dil'],
                                                    2)
    all_reports.loc[:, 'bookvalueplusdividend'] = round(
        all_reports['persharebookvalue'] + all_reports['pershareDividend'], 2)
    all_reports.loc[:, 'currentRatio'] = round(all_reports['totalCurrentAssets'] / all_reports['totalCurrentLiabilities'], 2)
    all_reports.loc[:, 'equityRatio'] = round(
        (all_reports['totalShareholderEquity'] / all_reports['totalAssets']) * 100, 2)
    all_reports.loc[:, 'ROE'] = round((all_reports['netIncome'] / all_reports['totalShareholderEquity']) * 100, 2)
    all_reports.loc[:, 'ROA'] = round((all_reports['netIncome'] / all_reports['totalAssets']) * 100, 2)
    capital_employed = all_reports['totalAssets'] - all_reports['totalCurrentLiabilities']
    all_reports.loc[:, 'ROCE'] = round((all_reports['ebit'] / capital_employed) * 100, 2)
    all_reports.loc[:, 'ebitMargin'] = round((all_reports['ebit'] / all_reports['totalRevenue']) * 100, 2)
    all_reports.loc[:, 'netProfitMargin'] = round((all_reports['netIncome'] / all_reports['totalRevenue']) * 100, 2)
    all_reports.loc[:, 'equityleverage'] = round(
        (all_reports['longTermDebtNoncurrent'] / all_reports['totalShareholderEquity']), 2)
    all_reports['reportedEPS'] = all_reports['reportedEPS'].astype(float)
    all_reports.loc[:, 'KGV'] = all_reports['avg_Kurs'] / all_reports['reportedEPS']
    all_reports.loc[:, 'KBV'] = all_reports['avg_Kurs'] / (
            all_reports['totalShareholderEquity'] / all_reports['shares_dil'])
    all_reports.loc[:, 'KUV'] = all_reports['avg_Kurs'] / all_reports['pershareRevenue']
    all_reports.loc[:, 'KCV'] = all_reports['avg_Kurs'] / all_reports['pershareFreeCashflow']
    all_reports.loc[:, 'dividendYield'] = round(
        ((all_reports['dividendPayout'] / all_reports['shares_dil']) / all_reports['avg_Kurs']) * 100, 2)
    return all_reports


def create_fundamentals(all_reports):
    keep = ['totalRevenue', 'netIncome', 'operatingCashflow', 'freeCashflow', 'ebit', 'longTermDebtNoncurrent',
            'pershareRevenue', 'reportedEPS', 'pershareOperativerCashflow', 'pershareFreeCashflow',
            'persharebookvalue', 'pershareDividend', 'bookvalueplusdividend', 'currentRatio', 'equityRatio',
            'ROE', 'ROA', 'ROCE', 'ebitMargin', 'netProfitMargin', 'equityleverage', 'shares_dil',
            'year', 'avg_Kurs', 'KGV', 'KBV', 'KUV', 'KCV', 'dividendYield']

    col_to_drop = [col for col in all_reports.columns if col not in keep]
    all_reports.drop(columns=col_to_drop, inplace=True)
    all_reports = all_reports[keep]

    all_reports = all_reports.set_index('year')
    all_reports = all_reports.copy().transpose()
    all_reports = all_reports[sorted([col for col in all_reports.columns if col != 'TTM']) + ['TTM']]

    return all_reports

def calculate_growth_rate(series,period):
  if period < len(series)-1:
    return ((series.iloc[-2] / series.iloc[-(period+2)]) ** (1 / period) -1)*100
  else:
    return None

def calculate_mean(series,period):
  if period < len(series)-1:
    return series.iloc[-(period+1):-1].mean()
  else:
    return None

# ggdata = gdata.iloc[9:]

def management(gdata,balance_qu):
  available_years = len(gdata) - 2
  periods = [1,3,5,8,13]
  valid_periods = [period for period in periods if period < available_years]

  # Add maximum period die möglich ist, wenn 13 Jahre nicht möglich
  if len(valid_periods) < len(periods):
    valid_periods.append(available_years)



  management_data = {'MEANS': [f"{period} Jahr(e)" for period in valid_periods] + ['mean']
  }

  metrics = {
      'ROE': 'ROE',
      'ROCE': 'ROCE'
    }

  verschuldungsgrad = round((balance_qu['longTermDebtNoncurrent'].iloc[0] / gdata['ebit']).iloc[-1], 2)

  for metric_name,column_name in metrics.items():
    means = []
    for period in valid_periods:
      mean = calculate_mean(gdata[column_name],period)
      means.append(mean)
    mean_mean = sum(means) / len(means) if any(means) else None
    means.append(mean_mean)
    management_data[metric_name] = means

  management_data['LT DEBT/EBIT'] = verschuldungsgrad
  return  pd.DataFrame(management_data)

def wachstum(gdata):
  available_years = len(gdata) - 2
  periods = [1,3,5,8,13]
  valid_periods = [period for period in periods if period < available_years]

  # Add maximum period die möglich ist, wenn 13 Jahre nicht möglich
  if len(valid_periods) < len(periods):
    valid_periods.append(available_years)

  growth_data = {'WACHSTUM PER SHARE': [f"{period} Jahr(e)" for period in valid_periods] + ['mean']
  }

  metrics = {
        'EPS': 'reportedEPS',
        'BOOK + DIV': 'bookvalueplusdividend',
        'REVENUE': 'pershareRevenue',
        'OPCASHFOW': 'pershareOperativerCashflow',
        'FCASHFLOW': 'pershareFreeCashflow'
    }

  for metric_name,column_name in metrics.items():
    growth_rates = []
    for period in valid_periods:
      growth_rate = calculate_growth_rate(gdata[column_name],period)
      growth_rates.append(growth_rate)
    mean_growth_rate = sum(growth_rates) / len(growth_rates) if any(growth_rates) else None
    growth_rates.append(mean_growth_rate)
    growth_data[metric_name] = growth_rates
      
  return  pd.DataFrame(growth_data)


def bewertung(gdata):
    kgv = gdata['KGV']
    kbv = gdata['KBV']
    kuv = gdata['KUV']
    fcf = gdata['freeCashflow']

    bewertung = ['KGV', 'KBV', 'KUV']

    fcfTTm = fcf.iloc[-1]
    fcf3y = fcf.iloc[-4:-1].mean()
    fcf5y = fcf.iloc[-6:-1].mean()
    fcf8y = fcf.iloc[-9:-1].mean()

    kgvTTm = kgv.iloc[-1]
    kgv3y = kgv.iloc[-4:-1].mean()
    kgv5y = kgv.iloc[-6:-1].mean()
    kgv8y = kgv.iloc[-9:-1].mean()

    kbvTTm = kbv.iloc[-1]
    kbv3y = kbv.iloc[-4:-1].mean()
    kbv5y = kbv.iloc[-6:-1].mean()
    kbv8y = kbv.iloc[-9:-1].mean()

    kuvTTm = kuv.iloc[-1]
    kuv3y = kuv.iloc[-4:-1].mean()
    kuv5y = kuv.iloc[-6:-1].mean()
    kuv8y = kuv.iloc[-9:-1].mean()

    means_fcf = [fcfTTm, fcf3y, fcf5y, fcf8y]
    means_kgv = [kgvTTm, kgv3y, kgv5y, kgv8y]
    means_kbv = [kbvTTm, kbv3y, kbv5y, kbv8y]
    means_kuv = [kuvTTm, kuv3y, kuv5y, kuv8y]

    df = pd.DataFrame(
        {'MEANS': ['TTM', '3 Jahre', '5 Jahre', '8 Jahre'], 'FreeCashflow': means_fcf, 'KGV': means_kgv,
         'KBV': means_kbv, 'KUV': means_kuv})

    return df

def overview_df(overview,balance_qu):
    name = overview['Name']
    sector = overview['Sector']
    ficalyearending = overview['FiscalYearEnd']
    latestquater = overview['LatestQuarter']
    mcap = overview['MarketCapitalization']
    shares = overview['SharesOutstanding']
    currentDebt = balance_qu['currentDebt'].iloc[0]
    LT_DEBT = balance_qu['longTermDebtNoncurrent'].iloc[0]
    CASH = balance_qu['cashAndShortTermInvestments'].iloc[0]
    dividentyield = overview['DividendYield']


    df = pd.DataFrame(
        {'NAME': name,
         'SEKTOR': sector,
         'FISCAL YEAR ENDING': ficalyearending,
         'LASTQUATER': latestquater,
         'MARKETCAP': mcap,
         'SHARES': shares,
         'ST_DEBT': currentDebt,
         'LT_DEBT': LT_DEBT,
         'CASH':CASH,
         'YIELD': dividentyield,
         })

    df = df.T

    for idx, row in df.iterrows():
        if idx == 'MARKETCAP':
            df.loc[idx, 0] = pd.to_numeric(df.loc[idx, 0]) / 1000000000
            df.loc[idx, 0] = "{:,.0f} Mrd".format(row[0])
        elif idx == 'SHARES':
            df.loc[idx, 0] = pd.to_numeric(df.loc[idx, 0]) / 1000000
            df.loc[idx, 0] = "{:,.0f} Mio".format(row[0])
        elif idx == 'LT_DEBT' or idx == 'ST_DEBT' or idx == 'CASH':
            df.loc[idx, 0] = pd.to_numeric(df.loc[idx, 0])
            df.loc[idx, 0] = "$ {:,.0f} Mio".format(row[0])
        elif idx == 'YIELD':
            df.loc[idx, 0] = pd.to_numeric(df.loc[idx, 0], errors='coerce')
            if pd.notna(df.loc[idx,0]):
                df.loc[idx,0] = df.loc[idx,0] * 100
                df.loc[idx, 0] = "{:,.2f} %".format(row[0])

    return df

def qualitaet(overview,gdata):
  netProfitMargin = pd.to_numeric(overview['ProfitMargin'])*100
  ebitMargin = pd.to_numeric(overview['OperatingMarginTTM'])*100
  ROE = pd.to_numeric(overview['ReturnOnEquityTTM'])*100
  ROA = pd.to_numeric(overview['ReturnOnAssetsTTM'])*100
  ROCE = gdata['ROCE'].iloc[-1]
  Eigenkapitalquote = gdata['equityRatio'].iloc[-1]
  Liquiditätsgrad = gdata['currentRatio'].iloc[-1]
  equityleverage = gdata['equityleverage'].iloc[-1]
  AusschuettungsquoteGewinn = (gdata['pershareDividend'].iloc[-1]/gdata['reportedEPS'].iloc[-1])*100
  AusschuettungsquoteFreeCashflow = (gdata['pershareDividend'].iloc[-1]/gdata['pershareFreeCashflow'].iloc[-1])*100

  df = pd.DataFrame(
      {'netProfitMargin': netProfitMargin,
        'ebitMargin': ebitMargin,
        'Eigenkapitalrendite': ROE,
        'Eigenkapitalquote':Eigenkapitalquote,
        'ReturnOnAssets': ROA,
        'ROCE': ROCE,
        'Liquiditätsgrad':Liquiditätsgrad,
        'Verschuldungsgrad': equityleverage,
        'PayoutRatioNetProfit': AusschuettungsquoteGewinn,
        'PayoutRatioFreeCF': AusschuettungsquoteFreeCashflow
       })

  df = df.T

  return df


