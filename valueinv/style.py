import pandas as pd
hide_style = """
            <style>
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
"""

def highlight_15(s):
    if s >= 15:
        props = "background-color: #66cdaa"
        return props
    elif 10 <= s < 15:
        props = "background-color: orange"
        return props
    elif s < 10:
        props = "background-color: lightred"
        return props

def highlight_10(s):
    if s >= 10:
        props = "background-color: #66cdaa"
        return props
    elif 5 <= s < 10:
        props = "background-color: orange"
        return props
    elif s < 5:
        props = "background-color: lightred"
        return props


def equityleverage(s):
    if s >=3:
        props = "background-color: lightred"
        return props
    elif 1 < s < 3:
        props = "background-color: orange"
        return props
    elif s <= 1:
        props = "background-color: #66cdaa"
        return props

def highlight_equityratio(s):
    if s <= 0:
        props = "background-color: lightred"
        return props
    elif 30 > s > 0:
        props = "background-color: orange"
        return props
    elif s >= 30:
        props = "background-color: #66cdaa"
        return props

def currentratio(s):
    if s >=2:
        props = "background-color: #66cdaa"
        return props
    elif 0.5 < s < 2:
        props = "background-color: orange"
        return props
    elif s <= 0.5:
        props = "background-color: lightred"
        return props



def highlight_payoutratio(s):
    if s >= 50:
        props = "background-color: lightred"
        return props
    elif 30 < s < 50:
        props = "background-color: orange"
        return props
    elif s <= 30:
        props = "background-color: #66cdaa"
        return props

def highlight_netprofitmargin(s):
    if s >= 10:
        props = "background-color: #66cdaa"
        return props
    elif 5 <= s < 10:
        props = "background-color: orange"
        return props
    elif s < 5:
        props = "background-color: lightred"
        return props

def highlight_ebitmargin(s):
    if s >= 20:
        props = "background-color: #66cdaa"
        return props
    elif 10 <= s < 20:
        props = "background-color: orange"
        return props
    elif s < 10:
        props = "background-color: lightred"
        return props

def highlight_wachstum(s):
    if s > 8:
        props = "background-color: #66cdaa"
        return props
    elif 0 < s < 8:
        props = "background-color: orange"
        return props
    elif s <= 0:
        props = "background-color: lightred"
        return props


def style_management(df):
    return df.style.map(highlight_15, subset=pd.IndexSlice[[df.index[-1]], ['ROCE', 'ROE']]) \
                                         .map(equityleverage, subset=pd.IndexSlice[[df.index[-1]], ['LT DEBT/EBIT']]) \
                                         .format({"ROCE": "{:,.2f} %" ,"ROE": "{:,.2f} %","LT DEBT/EBIT": "{:,.2f}"})\
                                         .hide(axis="index")\


def style_wachstum(df):
    return df.style.format({"EPS": "{:,.2f} %",
                            "BOOK + DIV": "{:,.2f} %",
                            "REVENUE": "{:,.2f} %",
                            "OPCASHFOW": "{:,.2f} %",
                            "FCASHFLOW": "{:,.2f} %"}) \
        .hide(axis="index")\
        .map(highlight_wachstum, subset=pd.IndexSlice[[df.index[-1]], ['EPS', 'BOOK + DIV', 'REVENUE', 'OPCASHFOW', 'FCASHFLOW']])

def style_bewertung(df):
    return df.style.format({"FreeCashflow": "{:,.0f}",
                            "KGV": "{:,.2f}",
                            "KBV": "{:,.2f}",
                            "KUV": "{:,.2f}"}) \
                    .hide(axis="index")


def style_qualitaet(df):
    def format_row_wise(styler, formatter):
        for row, row_formatter in formatter.items():
            row_num = styler.index.get_loc(row)

            for col_num in range(len(styler.columns)):
                styler._display_funcs[(row_num, col_num)] = row_formatter
        return styler

    formatters = {'netProfitMargin': lambda x: f"{x:,.2f} %",
                  'ebitMargin': lambda x: f"{x:,.2f} %",
                  'Eigenkapitalrendite': lambda x: f"{x:,.2f} %",
                  'Eigenkapitalquote': lambda x: f"{x:,.2f} %",
                  'ReturnOnAssets': lambda x: f"{x:,.2f} %",
                  'ROCE': lambda x: f"{x:,.2f} %",
                  'Liquiditätsgrad': lambda x: f"{x:,.2f}",
                  'Verschuldungsgrad': lambda x: f"{x:,.2f}",
                  'PayoutRatioNetProfit': lambda x: f"{x:,.2f} %",
                  'PayoutRatioFreeCF': lambda x: f"{x:,.2f} %"
                  }

    return format_row_wise(df.style, formatters).map(highlight_15, subset=pd.IndexSlice['Eigenkapitalrendite',:]) \
                                                .map(highlight_10, subset=pd.IndexSlice['ReturnOnAssets', :])\
                                                .map(highlight_15, subset=pd.IndexSlice['ROCE', :])\
                                                .map(highlight_equityratio, subset=pd.IndexSlice['Eigenkapitalquote', :])\
                                                .map(currentratio, subset=pd.IndexSlice['Liquiditätsgrad', :]) \
                                                .map(equityleverage, subset=pd.IndexSlice['Verschuldungsgrad', :]) \
                                                .map(highlight_payoutratio, subset=pd.IndexSlice['PayoutRatioNetProfit', :])\
                                                .map(highlight_payoutratio, subset=pd.IndexSlice['PayoutRatioFreeCF', :]) \
                                                .map(highlight_netprofitmargin, subset=pd.IndexSlice['netProfitMargin', :]) \
                                                .map(highlight_ebitmargin, subset=pd.IndexSlice['ebitMargin', :])

def style_overview(df):
    return df.style


def apply_funda(df):
    integer_rows = ['totalRevenue', 'netIncome', 'operatingCashflow', 'freeCashflow', 'ebit', 'longTermDebtNoncurrent',
                    'shares_dil']

    for row_name, row in df.iterrows():
        for col in df.columns:
            if row.name in integer_rows:
                df.loc[row_name, col] = "{:,.0f}".format(row[col])
            else:
                df.loc[row_name, col] = "{:,.2f}".format(row[col])
    return df.style


def set_table_styles(styled_df):
    return styled_df.set_table_styles([{'selector': 'th', 'props': [('font-weight', 'bold'), ('font-size', '11pt')]},
                                        {'selector': 'thead th', 'props': [('border-bottom', '2pt solid white')]},
                                        {'selector': 'tbody tr td:first-child', 'props': [('font-weight', 'bold')]},
                                        {'selector': 'td, th', 'props': [('border', 'none'),
                                                                         ('max-width', '200x'),
                                                                         ('white-space', 'nowrap'),
                                                                         ('overflow', 'hidden'),
                                                                         ('text-overflow','ellipsis')]},
                                        {'selector': 'thead th', 'props': [('border-bottom', '2pt solid white')]}
                                        ], overwrite=False)
