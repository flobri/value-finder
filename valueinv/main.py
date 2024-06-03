import datetime

import pandas as pd
import plotly.graph_objs as go
import streamlit as st

from process_data import convert_to_numeric, process_data, calculate_metrics, caculate_avg_price_by_year, \
    create_fundamentals, create_ttm_dataframe, management, wachstum, overview_df, qualitaet, bewertung
from style import style_management, hide_style, set_table_styles, apply_funda, style_wachstum, style_overview, \
    style_qualitaet, style_bewertung
from load_data import get_data,split_reports, create_dataframe

API_KEY = st.secrets["api_key"]
# ticker = 'AAPL'


# Dashboard
st.set_page_config(page_title="Value Finder", page_icon=":chart:", layout='wide')
st.markdown(hide_style,unsafe_allow_html=True)
st.title('Value Finder')
        
with st.container():
    col1, col2 = st.columns((1, 3))
    with col1:
        ticker = st.text_input('', placeholder='Tickersymbol')
        if ticker:
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
    with col2:
        if ticker:
            description = overview['Description'].iloc[0]
            st.write(description)
    if ticker:            
        tab0, tab1, tab2 = st.tabs(["Übersicht", "Historical Data", "Graphs"])
        with tab0:
            left_col, mid_col, right_col = st.columns((2, 4, 2))
            with left_col:
                st.subheader("Overview")
                sty_overview = style_overview(overview_df)
                sty_overview = set_table_styles(sty_overview)
                html = sty_overview.to_html(Index=False)
                html = html.replace("<thead>", "<thead style='display:none;'>")
                st.write(html, unsafe_allow_html=True)
    
                st.subheader("Qualität")
                # print(qualitaet_df)
                sty_qualitaet = style_qualitaet(qualitaet_df)
                sty_qualitaet = set_table_styles(sty_qualitaet)
                html = sty_qualitaet.to_html(Index=False)
                html = html.replace("<thead>", "<thead style='display:none;'>")
                st.write(html, unsafe_allow_html=True)
    
            with mid_col:
                # st.markdown("""
                #     <style>
                #     .reportview-container .main .block-container{
                #         max-width: 100%;
                #         padding-top: 2rem;
                #         padding-right: 2rem;
                #         padding-left: 2rem;
                #         padding-bottom: 2rem;
                #     }
                #     @media (max-width: 768px) {
                #         .reportview-container .main .block-container{
                #             padding-top: 1rem;
                #             padding-right: 1rem;
                #             padding-left: 1rem;
                #             padding-bottom: 1rem;
                #         }
                #     }
                #     </style>
                # """, unsafe_allow_html=True)
    
                plot_data = gdata.copy()
                current_year = datetime.datetime.now().year
                gdata.index = gdata.index.to_series().replace('TTM', current_year)
    
                price = go.Scatter(x=data_an['Date'], y=data_an['Adj Close'], mode='lines', name='Price',
                                   yaxis='y2')
                cashflow_bar = go.Bar(x=plot_data.index, y=plot_data['pershareFreeCashflow'],
                                      name='FreeCashflow je Share', yaxis='y1')
                netIncome_bar = go.Bar(x=plot_data.index, y=plot_data['reportedEPS'],
                                       name='NetIncome je Share',
                                       yaxis='y1')
                revenue_bar = go.Bar(x=plot_data.index, y=plot_data['pershareRevenue'],
                                     name='Revenue je Share',
                                     yaxis='y1')
    
                layout = go.Layout(
                    title='FreeCashflow vs. Price',
                    xaxis=dict(title='', tickfont=dict(size=16)),
                    yaxis=dict(title='Price', title_font=dict(size=16)),
                    yaxis2=dict(title='FCF & EPS', side='right', overlaying='y', title_font=dict(size=16)),
                    legend=dict(x=0.00, y=1.18, orientation='h', font=dict(size=16))
                )
    
                fig0 = go.Figure(data=[price, netIncome_bar, cashflow_bar, revenue_bar], layout=layout)
                st.plotly_chart(fig0, use_container_width=True)
    
            
                kpis = ['KGV', 'KBV', 'KUV']
                kpi = st.radio("", options=kpis, horizontal=True, index=kpis.index('KGV'))
                jahre = gdata.index.to_list()
                jahre_str = [str(jahr) if jahr != 'TTM' else f"{jahr}" for jahr in jahre]
                print(data_an)
                kgv = gdata['KGV']
                kbv = gdata['KBV']
                kuv = gdata['KUV']
                if kpi == 'KGV':
                    avg_kgv_plot_7y = kgv.iloc[-8:].mean()
                    avg_kgv_plot_5y = kgv.iloc[-6:].mean()
                    avg_kgv_plot_3y = kgv.iloc[-4:].mean()
    
                    pe_line = go.Scatter(x=jahre_str, y=kgv, mode='lines', name='P/E-Ratio',
                                         line=dict(width=3))
    
                    avg_line = go.Scatter(x=jahre_str, y=[avg_kgv_plot_7y] * len(jahre_str), mode='lines',
                                          name='avg 7 years', line=dict(width=3))
    
                    avg_line_3 = go.Scatter(x=jahre_str, y=[avg_kgv_plot_5y] * len(jahre_str), mode='lines',
                                            name='avg 5 years', line=dict(width=3))
                    avg_line_2 = go.Scatter(x=jahre_str, y=[avg_kgv_plot_3y] * len(jahre_str), mode='lines',
                                            name='avg 3 years', line=dict(width=3))
                    layout = go.Layout(title='Historisches P/E-RATIO',
                                       xaxis=dict(title='', tickfont=dict(size=16)),
                                       yaxis=dict(title='P/E-Ratio', title_font=dict(size=16)),
                                       legend=dict(x=0.2, y=1.1, orientation='h', font=dict(size=16)), )
    
                    fig1 = go.Figure(data=[pe_line, avg_line, avg_line_3, avg_line_2], layout=layout)
                    st.plotly_chart(fig1, use_container_width=True)
                if kpi == 'KBV':
                    avg_kbv_plot_7y = kbv.iloc[-8:].mean()
                    avg_kbv_plot_5y = kbv.iloc[-6:].mean()
                    avg_kbv_plot_3y = kbv.iloc[-4:].mean()
    
                    pe_line = go.Scatter(x=jahre_str, y=kbv, mode='lines', name='P/B-Ratio',
                                         line=dict(width=3))
    
                    avg_line = go.Scatter(x=jahre_str, y=[avg_kbv_plot_7y] * len(jahre_str), mode='lines',
                                          name='avg 7 years', line=dict(width=3))
    
                    avg_line_3 = go.Scatter(x=jahre_str, y=[avg_kbv_plot_5y] * len(jahre_str), mode='lines',
                                            name='avg 5 years', line=dict(width=3))
                    avg_line_2 = go.Scatter(x=jahre_str, y=[avg_kbv_plot_3y] * len(jahre_str), mode='lines',
                                            name='avg 3 years', line=dict(width=3))
                    layout = go.Layout(title='Historisches P/B-RATIO',
                                       xaxis=dict(title='', tickfont=dict(size=16)),
                                       yaxis=dict(title='P/B-Ratio', title_font=dict(size=16)),
                                       legend=dict(x=0.2, y=1.1, orientation='h', font=dict(size=16)), )
    
                    fig2 = go.Figure(data=[pe_line, avg_line, avg_line_3, avg_line_2], layout=layout)
                    st.plotly_chart(fig2, use_container_width=True)
                if kpi == 'KUV':
                    avg_kuv_plot_7y = kuv.iloc[-8:].mean()
                    avg_kuv_plot_5y = kuv.iloc[-6:].mean()
                    avg_kuv_plot_3y = kuv.iloc[-4:].mean()
    
                    pe_line = go.Scatter(x=jahre_str, y=kuv, mode='lines', name='P/R-Ratio',
                                         line=dict(width=3))
    
                    avg_line = go.Scatter(x=jahre_str, y=[avg_kuv_plot_7y] * len(jahre_str), mode='lines',
                                          name='avg 7 years', line=dict(width=3))
    
                    avg_line_3 = go.Scatter(x=jahre_str, y=[avg_kuv_plot_5y] * len(jahre_str), mode='lines',
                                            name='avg 5 years', line=dict(width=3))
                    avg_line_2 = go.Scatter(x=jahre_str, y=[avg_kuv_plot_3y] * len(jahre_str), mode='lines',
                                            name='avg 3 years', line=dict(width=3))
                    layout = go.Layout(title='Historisches P/R-RATIO',
                                       xaxis=dict(title='', tickfont=dict(size=16)),
                                       yaxis=dict(title='P/R-Ratio', title_font=dict(size=16)),
                                       legend=dict(x=0.2, y=1.1, orientation='h', font=dict(size=16)), )
    
                    fig3 = go.Figure(data=[pe_line, avg_line, avg_line_3, avg_line_2], layout=layout)
                    st.plotly_chart(fig3, use_container_width=True)
    
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
            pass


    else:
        st.write("Enter a US-Stock Ticker.")
