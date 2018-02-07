import requests
from bs4 import BeautifulSoup as bs
import json
import csv
import time
import os
import sys

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36'}
headers['Host'] = 'www.funda.nl'
headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'
base_url = 'https://www.funda.nl'

with open('logs.txt', 'w') as LOG:
    LOG.write('house_count' + ',' + 'result' + ',' + 'page' + '\n')

with open('proxies.txt') as ff:
    proxy_list = [i.replace('\n', '') for i in ff.readlines()]


def rm_space(S):
    return " ".join(S.split())


def get_proxy(count_p):
    proxy_line = proxy_list[count_p]
    proxy_splitted = proxy_line.split(':')
    proxy_string = proxy_splitted[2] + ':' + proxy_splitted[3] + '@' + proxy_splitted[0] + ':' + proxy_splitted[1]
    proxies = {"https": "https://%s" % proxy_string}
    return proxies

def repeat(feature = '', h3=''):
    new  = h3 + '_' + feature
    return new


session = requests.Session()

house_count = 0
page = 0
count_proxy = -1
flag_quit = False
full_dic = {}

while 1:
    if flag_quit:
    	break
    page += 1
    if house_count > 10:
        break
    count_proxy += 1
    if count_proxy == len(proxy_list):
        count_proxy = 0
    proxies = get_proxy(count_proxy)
    url = 'https://www.funda.nl/koop/heel-nederland/p%s/' % str(page)
    while 1:
        try:
            res = session.get(url, headers=headers, proxies=proxies, timeout=10, allow_redirects=False)
            break
        except Exception as e:
            print(e)
            continue
    soup = bs(res.content, "lxml")
    result_list = [base_url + i['href'] for i in soup.find_all('a', {'data-object-url-tracking': 'resultlist'})]

    # print(len(result_list))

    try:
        next_button = soup.find_all('a', {'rel': 'next'})[0]
    except:
        print('\n> last page reached !')
        break

    result_list = list(set(result_list))
    for result in result_list:
        try:
            result_id = result.split('/')[-2]
            # print(result_id)

            house_count += 1
            # if house_count == 10:
            # 	flag_quit = True

            count_proxy += 1
            if count_proxy == len(proxy_list):
                count_proxy = 0
            while 1:
                try:
                    h_res = session.get(result, headers=headers, proxies=proxies, timeout=10, allow_redirects=False)
                    break
                except:
                    continue
            h_soup = bs(h_res.content, "lxml")
            # print (h_soup)
            address_bloc = h_soup.find_all('h1', {'class': 'object-header__address'})[0].contents

            address = address_bloc[0].replace('\r\n', '').strip()
            street_number = ''
            for A in address.split(' '):
                if A.isdigit():
                    street_number = A
                    sn_index = address.split(' ').index(street_number)
            street_name = ' '.join(address.split(' ')[0:sn_index]).strip()
            street_name_ext = ' '.join(address.split(' ')[sn_index + 1:]).strip()
            zip_code = ' '.join(address_bloc[1].text.split(' ')[0:2]).replace(' ', '').strip()
            zip_code_number = zip_code[0:4]
            zip_letter = zip_code[4:]
            city = ' '.join(address_bloc[1].text.split(' ')[2:])

            details_dic = {}
            h3_headers = h_soup.find_all('h3', {'class': 'object-kenmerken-list-header'})

            details_blocs = h_soup.find_all('dl', {'class': 'object-kenmerken-list'})
            for index, details_bloc in enumerate(details_blocs):
                h3 = h3_headers[index].text.strip()
                details_headers = []
                INDEX_LIST = []
                for II, DH_ in enumerate(details_bloc.find_all('dt')):
                    if not 'object-kenmerken-group-header' in str(DH_):
                        if DH_.text.strip().startswith('Huurprijs'):
                            details_headers.append(DH_.text.strip().split(' ')[0])
                        else:
                            details_headers.append(DH_.text.strip())
                    else:
                        INDEX_LIST.append(II)

                NEW_INDEX_LIST = []
                for KK, IL in enumerate(INDEX_LIST):
                    NEW_IL = IL - KK
                    NEW_INDEX_LIST.append(NEW_IL)

                details_values_ = [i for i in details_bloc.find_all('dd') if
                                   not 'object-kenmerken-group-list' in str(i)]
                # print(NEW_INDEX_LIST)
                for IL in NEW_INDEX_LIST:
                    # print(details_values_[IL])
                    del details_values_[IL]

                # details_headers  = [i.text.strip() for  i in  details_bloc.find_all('dt') ]
                details_values_ = [i.text.strip() for i in details_values_]

                details_values = []
                for det in details_values_:
                    if 'm�' in det:
                        details_values.append(det.split('m�')[0].strip())
                    elif 'm�' in det:
                        details_values.append(det.split('m�')[0].strip())
                    else:
                        details_values.append(det)

                for DH, DV in zip(details_headers, details_values):
                    if DV.startswith(DH):
                        DV = DV.split(DH)[1].strip()
                    if DH.lower() != 'vraagprijs':
                        if 'Aantal kamers' in DH:
                            if '(' in DV:
                                kamers = DV.split('(')[0].replace('kamers', '').strip()
                                slaapkamers = DV.split('(')[1].replace('slaapkamers', '').replace(')', '').strip()
                                details_dic['kamers'] = rm_space(kamers)
                                details_dic['slaapkamers'] = rm_space(slaapkamers)
                        elif 'energielabel' in DH.lower():
                            if 'Wat betekent dit?' in DV:
                                energy = DV.split('Wat betekent dit?')[0].strip()
                            else:
                                energy = DV
                            details_dic[DH] = rm_space(energy[0:1])
                        else:
                            if DH in details_dic:
                                DH = repeat(feature=DH,h3=h3)
                                details_dic[DH] = rm_space(DV)
                            else:
                                details_dic[DH] = rm_space(DV)

                            # print(len(details_headers), len(details_values))

            all_images_bloc = h_soup.find_all('div', {'class': 'object-media-foto'})
            all_images_list = []
            for IMG in all_images_bloc:
                try:
                    all_images_list.append(IMG.find_all('img')[0]['data-lazy'])
                except:
                    all_images_list.append(IMG.find_all('img')[0]['src'])
            all_images = ' | '.join(all_images_list)
            try:
                phone = [i for i in h_soup.find_all('a', href=True) if 'tel:' in i['href']][0]['href'].split('tel:')[1]
            except:
                phone = ''

            try:
                description = h_soup.find_all('div', {'class': 'object-description-body'})[0].text.strip()
            except:
                description = ''

            try:
                price_bloc = h_soup.find_all('strong', {'class': 'object-header-price'})[0].text.strip().replace('�',
                                                                                                                 '').strip()
            except:
                price_bloc = ''

            try:
                price = price_bloc.split(' ')[0]
            except:
                price = ''
            try:
                price_type = price_bloc.split(' ')[1]
            except:
                price_type = ''

            # print(price, price_type)

            # print(phone)

            details_dic['Address'] = rm_space(address)
            details_dic['Street_Name'] = rm_space(street_name)
            details_dic['Street_Number'] = rm_space(street_number)
            details_dic['Street_Name_Extension'] = rm_space(street_name_ext)
            details_dic['Zip_Code'] = rm_space(zip_code)
            details_dic['Zip_Number'] = rm_space(zip_code_number)
            details_dic['Zip_Letter'] = rm_space(zip_letter)
            details_dic['City'] = rm_space(city)
            details_dic['Images'] = rm_space(all_images)
            details_dic['Phone'] = rm_space(phone)
            details_dic['Description'] = rm_space(description)
            details_dic['Price'] = rm_space(price)
            details_dic['Price_Type'] = rm_space(price_type)
            details_dic['URL'] = rm_space(result)

            details_dic['huur/koop'] = 'koop'
            # print(details_dic)

            full_dic[result_id] = details_dic
            print(house_count, result, page)
            with open('logs.txt', 'a') as LOG:
                LOG.write(str(house_count) + ',' + result + ',' + str(page) + '\n')

                # if flag_quit:
                # 	break
        except:
            print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
            pass

print('\npreparing the csv file ...')

ALL_COLS = []
for k, v in full_dic.items():
    for COLS in v:
        ALL_COLS.append(COLS)

# print(ALL_COLS)
ALL_COLS = list(set(ALL_COLS))

# print(ALL_COLS)


# CSV FILE HEADER :
H = []
for COL in ALL_COLS:
    H.append(COL)
with open('funda_data_sale_feb7_18.csv', 'w', newline="", encoding='utf-8') as outfile:
    csvwriter = csv.writer(outfile, delimiter=';')
    csvwriter.writerow(H)

for k, v in full_dic.items():
    h = ['' for i in range(len(H))]
    for COLS in v:
        INDEX = H.index(COLS)
        h[INDEX] = v[COLS]
    with open('funda_data_sale_feb7_18.csv', 'a', newline="", encoding='utf-8') as outfile:
        csvwriter = csv.writer(outfile, delimiter=';')
        csvwriter.writerow(h)
