import datetime
import json
import pandas as pd
import plotly.graph_objs as go
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

from process_data import convert_to_numeric, process_data, calculate_metrics, caculate_avg_price_by_year, \
    create_fundamentals, create_ttm_dataframe, management, wachstum, overview_df, qualitaet, bewertung
from style import style_management, hide_style, set_table_styles, apply_funda, style_wachstum, style_overview, \
    style_qualitaet, style_bewertung
from load_data import get_data,split_reports, create_dataframe

API_KEY = st.secrets["api_key"]

with open('valueinv/dic_ticker.json','r') as fp:
  dic_ticker = json.load(fp)


# Dashboard
st.set_page_config(page_title="Value Finder", page_icon=":chart:", layout='wide')
st.markdown(hide_style,unsafe_allow_html=True)
st.title('Value Finder')
        

with st.container():
    col1, col2 = st.columns((1, 3))
    with col1:
        ticker = st.selectbox('', placeholder='Tickersymbol', options=dic_ticker)
        if ticker:
            try:
                # Laden der Daten
                overview, balance, cashflow, income, earnings = get_data(ticker, API_KEY)

                # Aufbereiten der Daten
                # Convert to numeric
                exception_columns = ['fiscalDateEnding', 'reportedCurrency', 'ReportType']
                income = convert_to_numeric(income, exception_columns)
                balance = convert_to_numeric(balance, exception_columns)
                cashflow = convert_to_numeric(cashflow, exception_columns)
                earnings['reportedEPS'] = pd.to_numeric(earnings['reportedEPS'])

                # Fasse historische Daten aus Api zu einem dataframe je Reporttype zusammen
                all_reports_an, all_reports_qu, balance_qu = process_data(cashflow, income, balance, earnings)

                # Verbinde jährliche Daten mit TTM Daten aus quaterly reported data
                all_reports_an, data_an = caculate_avg_price_by_year(all_reports_an, ticker)
                ttm, data_qu = create_ttm_dataframe(all_reports_qu, balance_qu, ticker)
                all_reports = pd.concat([all_reports_an, ttm]).reset_index(drop=True)

                # Berechne alle relevanten Kennzahlen und generiere finalen Dataframe
                all_reports = calculate_metrics(all_reports)
                fundamentals = create_fundamentals(all_reports)
                gdata = fundamentals.T
                management = management(gdata, balance_qu)
                wachstum = wachstum(gdata)
                bewertung = bewertung(gdata)
                overview_df = overview_df(overview, balance_qu)
                qualitaet_df = qualitaet(overview, gdata)
            except Exception as e:
                st.warning("Keine Daten vorhanden")
    with col2:
        if ticker:
            try:
                description = overview['Description'].iloc[0]
                name = overview['Name'].iloc[0].replace(' ', '+')
                sec_url = f"https://www.sec.gov/cgi-bin/browse-edgar?company={name}&match=starts-with&filenum=&State=&Country=&SIC=&myowner=exclude&action=getcompany"

                
                st.write(description)
                st.write(f"""<div style="width:100%;"><a href="{sec_url}" style="float:center">SEC Filings</a></div>""", unsafe_allow_html=True)

            
            except Exception as e:
                st.warning("Keine Daten vorhanden")
    if ticker:
        
        try:
            tab0, tab1, tab2 = st.tabs(["Übersicht", "Historical Data", "Graphs"])
            with tab0:
                left_col, mid_col, right_col = st.columns((0.9,2,1.5))
                with left_col:
                    st.subheader("Overview")
                    sty_overview = style_overview(overview_df)
                    sty_overview = set_table_styles(sty_overview)
                    html = sty_overview.to_html(Index=False)
                    html = html.replace("<thead>", "<thead style='display:none;'>")
                    st.write(html, unsafe_allow_html=True)
    
                    st.subheader("Qualität")
                    sty_qualitaet = style_qualitaet(qualitaet_df)
                    sty_qualitaet = set_table_styles(sty_qualitaet)
                    html = sty_qualitaet.to_html(Index=False)
                    html = html.replace("<thead>", "<thead style='display:none;'>")
                    st.write(html, unsafe_allow_html=True)
        
                with mid_col:
                    st.markdown("""
                        <style>
                        .reportview-container .main .block-container{
                            max-width: 100%;
                            padding-top: 2rem;
                            padding-right: 2rem;
                            padding-left: 2rem;
                            padding-bottom: 2rem;
                        }
                        @media (max-width: 768px) {
                            .reportview-container .main .block-container{
                                padding-top: 1rem;
                                padding-right: 1rem;
                                padding-left: 1rem;
                                padding-bottom: 1rem;
                            }
                        }
                        </style>
                    """, unsafe_allow_html=True)
        
                    plot = gdata.copy()
                    plot.reset_index(inplace=True)
                    plot.drop(columns= [col for col in plot.columns if col not in ['year','pershareFreeCashflow','pershareRevenue','reportedEPS']], inplace = True)
                    next_year = datetime.now().date().year +1
                    plot['date'] = pd.to_datetime(plot['year'].apply(lambda x: f"{x}-12-28" if x != 'TTM' else pd.Timestamp(f"{next_year}-01-01")))
                                                            
                    fig0,ax1 = plt.subplots(figsize=(12,8))
                    width = 40
                    # Bar Plots
                    adjust_pos = pd.Timedelta(days=width*1.5)
                    barFC = ax1.bar(plot['date']- adjust_pos, plot['pershareFreeCashflow'],width*2, label='FreeCashflow je Share')
                    barEPS = ax1.bar(plot['date'] , plot['reportedEPS'],width*2, label='EPS')
                    barR = ax1.bar(plot['date']+ adjust_pos, plot['pershareRevenue'],width*2, label='Revenue je Share')
                    
                    # Beschriftung Bar Plots
                    ax1.bar_label(barFC,label_type='edge',rotation=90,padding=3)
                    ax1.bar_label(barR,label_type='edge',rotation=90,padding=3)
                    ax1.bar_label(barEPS,label_type='edge',rotation=90,padding=3)
                    
                    #Achsenbeschriftung & Legende
                    ax1.set_ylabel('FCF, EPS und Revenue je Share')

                    # Price Chart
                    ax2= ax1.twinx()
                    line, = ax2.plot(data_an['Date'],data_an['Adj Close'], color='blue',linestyle='-', linewidth=2,label='Price')
                    ax2.set_ylabel('Price')
                                        
                    # x Achse beschriften
                    dates = plot['date'].tolist()
                    labes = [str(year) if year != 'TTM' else 'TTM' for year in plot['year']]
                    ax1.set_xticks(dates)
                    ax1.set_xticklabels(labes)                 

                    # Beschriftung LineChart
                    ax2.text(data_an.Date.iloc[-1], data_an['Adj Close'].iloc[-1],f"{round(float(data_an['Adj Close'].iloc[-1]),2)}", ha='left', va='bottom', fontsize=12, color='blue')
                    
                    #Legende
                    bars = [barFC, barEPS,barR, line]
                    labels = [bar.get_label() for bar in bars]
                    fig0.tight_layout()
                    fig0.legend(bars, labels, loc='upper center', bbox_to_anchor=(0.5, 0.95), ncol=4)
                    plt.title('FreeCashflow vs. Price')
                    plt.grid(True)
                    
                    st.pyplot(fig0)
    
    
                    kpis = ['KGV', 'KBV', 'KUV']
                    value = gdata.copy().reset_index(inplace=True)
                    value = gdata[['year','KGV','KUV','KBV']]
                    kgv = value['KGV']
                    kbv = value['KBV']
                    kuv = value['KUV']
                    kpi = st.radio("", options=kpis, horizontal=True, index=kpis.index('KGV'))
                     if kpi == 'KGV':
                      avg_kgv_plot_7y = kgv.iloc[-8:].mean()

                      avg_kgv_plot_5y = kgv.iloc[-6:].mean()
                      avg_kgv_plot_3y = kgv.iloc[-4:].mean()
                    
                      next_year = datetime.now().date().year +1
                      value['date'] = pd.to_datetime(value['year'].apply(lambda x: f"{x}-12-28" if x != 'TTM' else pd.Timestamp(f"{next_year}-01-01")))
                    
                      fig1,ax = plt.subplots(figsize=(10,6))
                      ax.plot(value['date'],value['KGV'], marker='o',label=col)
                    
                      dates = value['date'].tolist()
                      labes = [str(year) if year != 'TTM' else 'TTM' for year in value['year']]
                      ax.set_xticks(dates)
                      ax.set_xticklabels(labes) 
                      ax.set_ylabel('KGV')
                                       
                      ax.axhline(y=avg_kgv_plot_3y, color='red',linestyle='--', label='3y_mean')
                      ax.axhline(y=avg_kgv_plot_5y, color='blue',linestyle='--', label='5y_mean')
                      ax.axhline(y=avg_kgv_plot_7y, color='green',linestyle='--', label='7y_mean')
                    
                      ax.grid(True)
                      ax.legend()  
                      st.pyplot(fig1)
                    # if kpi == 'KBV':
                    #     avg_kbv_plot_7y = kbv.iloc[-8:].mean()
                    #     avg_kbv_plot_5y = kbv.iloc[-6:].mean()
                    #     avg_kbv_plot_3y = kbv.iloc[-4:].mean()
    
                    #     pe_line = go.Scatter(x=jahre_str, y=kbv, mode='lines', name='P/B-Ratio',
                    #                          line=dict(width=3))
    
                    #     avg_line = go.Scatter(x=jahre_str, y=[avg_kbv_plot_7y] * len(jahre_str), mode='lines',
                    #                           name='avg 7 years', line=dict(width=3))
    
                    #     avg_line_3 = go.Scatter(x=jahre_str, y=[avg_kbv_plot_5y] * len(jahre_str), mode='lines',
                    #                             name='avg 5 years', line=dict(width=3))
                    #     avg_line_2 = go.Scatter(x=jahre_str, y=[avg_kbv_plot_3y] * len(jahre_str), mode='lines',
                    #                             name='avg 3 years', line=dict(width=3))
                    #     layout = go.Layout(title='Historisches P/B-RATIO',
                    #                        xaxis=dict(title='', tickfont=dict(size=16)),
                    #                        yaxis=dict(title='P/B-Ratio', title_font=dict(size=16)),
                    #                        legend=dict(x=0.2, y=1.1, orientation='h', font=dict(size=16)), )
    
                    #     fig2 = go.Figure(data=[pe_line, avg_line, avg_line_3, avg_line_2], layout=layout)
                    #     st.plotly_chart(fig2, use_container_width=True)
                    # if kpi == 'KUV':
                    #     avg_kuv_plot_7y = kuv.iloc[-8:].mean()
                    #     avg_kuv_plot_5y = kuv.iloc[-6:].mean()
                    #     avg_kuv_plot_3y = kuv.iloc[-4:].mean()
    
                    #     pe_line = go.Scatter(x=jahre_str, y=kuv, mode='lines', name='P/R-Ratio',
                    #                          line=dict(width=3))
    
                    #     avg_line = go.Scatter(x=jahre_str, y=[avg_kuv_plot_7y] * len(jahre_str), mode='lines',
                    #                           name='avg 7 years', line=dict(width=3))
    
                    #     avg_line_3 = go.Scatter(x=jahre_str, y=[avg_kuv_plot_5y] * len(jahre_str), mode='lines',
                    #                             name='avg 5 years', line=dict(width=3))
                    #     avg_line_2 = go.Scatter(x=jahre_str, y=[avg_kuv_plot_3y] * len(jahre_str), mode='lines',
                    #                             name='avg 3 years', line=dict(width=3))
                    #     layout = go.Layout(title='Historisches P/R-RATIO',
                    #                        xaxis=dict(title='', tickfont=dict(size=16)),
                    #                        yaxis=dict(title='P/R-Ratio', title_font=dict(size=16)),
                    #                        legend=dict(x=0.2, y=1.1, orientation='h', font=dict(size=16)), )
    
                    #     fig3 = go.Figure(data=[pe_line, avg_line, avg_line_3, avg_line_2], layout=layout)
                    #     st.plotly_chart(fig3, use_container_width=True)
        
                with right_col:
                    st.subheader("Bewertung")
                    sty_bewertung = style_bewertung(bewertung)
                    sty_bewertung = set_table_styles(sty_bewertung)
                    st.write(sty_bewertung.to_html(), unsafe_allow_html=True)
    
                    st.subheader('Management')
                    sty_management = style_management(management)
                    sty_management = set_table_styles(sty_management)
                    st.write(sty_management.to_html(), unsafe_allow_html=True)
    
                    st.subheader("Wachstum")
                    sty_wachstum = style_wachstum(wachstum)
                    sty_wachstum = set_table_styles(sty_wachstum)
                    st.write(sty_wachstum.to_html(), unsafe_allow_html=True)
        
            with tab1:
                options = ['3 years', '5 years', '8 years', 'max']
                selected_years = st.radio("", options, horizontal=True, index=options.index('8 years'))
    
                if selected_years == 'max':
                    styled_fundamentals = apply_funda(fundamentals)
                    styled_fundamentals = set_table_styles(styled_fundamentals)
                    st.write(styled_fundamentals.to_html(), unsafe_allow_html=True)
    
                elif selected_years == '3 years':
                    fundamentals = fundamentals[fundamentals.columns[-3:]]
                    styled_fundamentals = apply_funda(fundamentals)
                    styled_fundamentals = set_table_styles(styled_fundamentals)
                    st.write(styled_fundamentals.to_html(), unsafe_allow_html=True)
    
                elif selected_years == '5 years':
                    fundamentals = fundamentals[fundamentals.columns[-5:]]
                    styled_fundamentals = apply_funda(fundamentals)
                    styled_fundamentals = set_table_styles(styled_fundamentals)
                    st.write(styled_fundamentals.to_html(), unsafe_allow_html=True)
    
                elif selected_years == '8 years':
                    fundamentals = fundamentals[fundamentals.columns[-8:]]
                    styled_fundamentals = apply_funda(fundamentals)
                    styled_fundamentals = set_table_styles(styled_fundamentals)
                    st.write(styled_fundamentals.to_html(), unsafe_allow_html=True)
        
            with tab2:
                plot = gdata.copy() 
                plot.index = plot.index.astype(str)


                col10,col11,col12 = st.columns(3)
                with col10:
                    fig4, ax = plt.subplots(figsize=(10, 6))
                    ax.plot(plot.index, plot['totalRevenue'], marker='o', label='Revenue')
                    ax.plot(plot.index, plot['operatingCashflow'], marker='o', label='Operating Cashflow')
                    ax.plot(plot.index, plot['netIncome'], marker='o', label='Net Profit')
                    ax.plot(plot.index, plot['freeCashflow'], marker='o', label='Free Cashflow')
                    
                    ax.text(plot.index[-1], plot['freeCashflow'][-1], f" {int(plot['freeCashflow'][-1])}", ha='left', va='center', fontsize=9,color='blue')
                    ax.text(plot.index[-1], plot['operatingCashflow'][-1], f" {int(plot['operatingCashflow'][-1])}", ha='left', va='center', fontsize=9,color='blue')
                    ax.text(plot.index[-1], plot['netIncome'][-1], f" {int(plot['netIncome'][-1])}", ha='left', va='center', fontsize=9,color='blue')
                    ax.text(plot.index[-1], plot['totalRevenue'][-1], f" {int(plot['totalRevenue'][-1])}", ha='left', va='center', fontsize=9,color='blue')
                
                    ax.set_title('Financial Performance')
                    ax.set_ylabel('Amount in Millions')
                    ax.legend()
                    ax.grid(True)
                    ax.set_xticks(plot.index)
                
                    st.pyplot(fig4)

                    fig7, ax = plt.subplots(figsize=(10, 6))
                    ax.plot(plot.index, plot['equityRatio'], marker='o', label='Eigenkapitalquote')
                    
                    for i in range(len(plot)):
                      ax.text(plot.index[i], plot['equityRatio'][i], f" {float(plot['equityRatio'][i])} %", ha='center', va='bottom', fontsize=9,color='blue')
                    
                    ax.set_title('Eingenkapitalentwicklung')
                    ax.legend()
                    ax.grid(True)
                    ax.set_xticks(plot.index)
                    st.pyplot(fig7)
               
                with col11:
                    fig5, ax = plt.subplots(figsize=(10, 6))
                    ax.plot(plot.index, plot['ROE'], marker='o', label='Eigenkapitalrendite')
                    ax.plot(plot.index, plot['ROA'], marker='o', label='Gesamtkapitalrendite')
                    ax.plot(plot.index, plot['ROCE'], marker='o', label='ROCE')
                    
                    
                    ax.text(plot.index[-1], plot['ROE'][-1], f" {float(plot['ROE'][-1])} %", ha='left', va='center', fontsize=9,color='blue')
                    ax.text(plot.index[-1], plot['ROA'][-1], f" {float(plot['ROA'][-1])} %", ha='left', va='center', fontsize=9,color='blue')
                    ax.text(plot.index[-1], plot['ROCE'][-1], f" {float(plot['ROCE'][-1])} %", ha='left', va='center', fontsize=9,color='blue')

                    ax.set_title('Kapitalrenditen')
                    ax.legend()
                    ax.grid(True)
                    ax.set_xticks(plot.index)
                    st.pyplot(fig5)

                    fig8, ax = plt.subplots(figsize=(10, 6))
                    ax.plot(plot.index, plot['shares_dil'], marker='o', label='dil. Shares Outstanding')
                    
                    for i in range(len(plot)):
                      ax.text(plot.index[i], plot['shares_dil'][i], f" {int(plot['shares_dil'][i])}", ha='center', va='bottom', fontsize=9,color='blue')
                    
                    ax.set_title('Shares')
                    ax.legend()
                    ax.grid(True)
                    ax.set_xticks(plot.index)
                    st.pyplot(fig8)     
                    
                with col12:
                    fig6, ax = plt.subplots(figsize=(10, 6))
                    ax.plot(plot.index, plot['ebitMargin'], marker='o', label='Ebit-Marge')
                    ax.plot(plot.index, plot['netProfitMargin'], marker='o', label='Netto-Marge')
                    
                    ax.text(plot.index[-1], plot['ebitMargin'][-1], f" {float(plot['ebitMargin'][-1])} %", ha='left', va='center', fontsize=9,color='blue')
                    ax.text(plot.index[-1], plot['netProfitMargin'][-1], f" {float(plot['netProfitMargin'][-1])} %", ha='left', va='center', fontsize=9,color='blue')
                    
                    ax.set_title('Gewinnmargen')
                    ax.legend()
                    ax.grid(True)
                    ax.set_xticks(plot.index)
                    st.pyplot(fig6)       
                    
                    fig9, ax = plt.subplots(figsize=(10, 6))
                    ax.plot(plot.index, plot['equityleverage'], marker='o', label='LT-Debt/Equity')
                    ax.axhline(y = 1, color = 'red', linestyle='--', linewidth=2)
                    
                    ax.axhline(y=management['LT DEBT/EBIT'].iloc[-1], color = 'orange', linestyle='-', linewidth=2, label='LT-Debt/EBIT')
                    ax.text(len(plot.index)/2,management['LT DEBT/EBIT'].iloc[-1],f"{float(management['LT DEBT/EBIT'].iloc[-1])}", ha='center', va='bottom', fontsize=12, color='blue')
                    
                    for i in range(len(plot)):
                      ax.text(plot.index[i], plot['equityleverage'][i], f" {float(plot['equityleverage'][i])}", ha='center', va='bottom', fontsize=9,color='black')
                    
                    ax.set_title('Verschuldungsgrad')
                    ax.legend()
                    ax.grid(True)
                    ax.set_xticks(plot.index)
                    st.pyplot(fig9)
                
        except Exception as e:
            st.warning("Keine Daten vorhanden")





    else:
        st.write("Enter a US-Stock Ticker.")
