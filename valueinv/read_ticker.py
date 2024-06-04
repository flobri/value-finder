import csv
import requests
import json
# from google.colab import files


# replace the "demo" apikey below with your own key from https://www.alphavantage.co/support/#api-key
CSV_URL = 'https://www.alphavantage.co/query?function=LISTING_STATUS&apikey=demo'

with requests.Session() as s:
    download = s.get(CSV_URL)
    decoded_content = download.content.decode('utf-8')
    cr = csv.reader(decoded_content.splitlines(), delimiter=',')
    my_list = list(cr)


listings = pd.DataFrame(my_list[1:], columns=my_list[0])

list_names = listings.apply(lambda x: f"({x.exchange}:{x.symbol}) {x['name']}", axis=1).to_list()
list_symbols = listings.symbol.to_list()

dict_ticker = dict(zip(list_names,list_symbols))

with open('dic_ticker.json','w') as fp:
  json.dump(dict_ticker,fp)

# files.download('dic_ticker.json')
