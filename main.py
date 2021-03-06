from __future__ import print_function, division
import requests
import json
import os
import math
import re
import sys
from time import sleep, time
from slackclient import SlackClient

VERSION = sys.version_info[0]

if VERSION == 2:
	from HTMLParser import HTMLParser
	html = HTMLParser()
else:
	import html

def load_from_json(file):
	try:
		with open(file, 'r') as myfile:
			return json.load(myfile)
	except IOError:
		with open(file, 'w') as myfile:
			json.dump({}, myfile)
		return {}

config = load_from_json('config.json')
location = config['location']
searches = config['searches']
zip_code = config['zipCode']
distance = config['distance']
max_price = config['maxPrice']
in_title = config['inTitle']
strict_match = config['strictMatch']
delay = config['delay']
width = config['width']
slack_token = config['slackToken']

headers = {
	'Connection': 'keep-alive',
	'Upgrade-Insecure-Requests': '1',
	'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36',
	'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
	'Accept-Encoding': 'gzip, deflate, br',
	'Accept-Language': 'en-US,en;q=0.9',
}

def center(text, spacer=' ', length=width, clear=False, display=True):
	if clear:
		os.system('cls' if os.name == 'nt' else 'clear')
	count = int(math.ceil((length - len(text)) / 2))
	if count > 0:
		if display:
			print(spacer * count + text + spacer * count)
		else:
			return (spacer * count + text + spacer * count)
	else:
		if display:
			print(text)
		else:
			return text

def header():
	center(' ', clear=True)
	center('Craigslist Monitor by @DefNotAvg')
	center('-', '-')

def smart_sleep(delay):
	if delay > 0:
		for a in range(delay, 0, -1):
			print('{}\r'.format(center('Sleeping for {} seconds...'.format(str(a)), display=False)), end='')
			sleep(1)
		center('Sleeping for {} seconds complete!'.format(str(delay)))

def gather_image(link):
	try:
		response = requests.get(link, headers=headers)
		content = response.content.decode('utf-8')
		return content.split('<img src="')[1].split('"')[0]
	except (requests.exceptions.ConnectionError, IndexError):
		return 'https://cdn.browshot.com/static/images/not-found.png'

def gather_items(query, items, current=None, page=1):
	result = dict(items)
	links = []
	prices = []
	params = (
		('query', query),
		('search_distance', distance),
		('postal', zip_code),
	)
	if max_price:
		params += (('max_price', max_price),)
	if current:
		params += (('s', current),)
	try:
		response = requests.get('https://{}.craigslist.org/search/sss'.format(location), headers=headers, params=params)
		content = response.content.decode('utf-8')
	except requests.exceptions.ConnectionError:
		return result, False
	try:
		range_to = content.split('<span class="rangeTo">')[1].split('</span>')[0]
		total_count = content.split('<span class="totalcount">')[1].split('</span>')[0]
	except IndexError:
		print(content)
		if VERSION == 2:
			center('Try using Python 3.7.3.')
		else:
			center('Try using Python 2.7.16.')
		quit()
	titles = re.findall(r'class="result-title hdrlnk">(.*?)</a>', content)
	data_ids = re.findall(r'data-id="(.*?)"', content)
	for data_id in data_ids:
		links.append('https://{}.craigslist.org/{}/{}.html'.format(location, content.split(data_id)[-4].split('craigslist.org/')[-1].split('/')[0], data_id))
		prices.append(content.split(data_id)[-2].split('<span class="result-price">')[1].split('</span>')[0])
	for item in zip(data_ids, titles, prices, links):
		if in_title:
			if strict_match:
				if query.lower() in html.unescape(item[1]).lower():
					result[item[0]] = {}
					result[item[0]]['title'] = item[1]
					result[item[0]]['price'] = item[2]
					result[item[0]]['link'] = item[3]
			else:
				if all(keyword.lower() in html.unescape(item[1]).lower() for keyword in query.split(' ')):
					result[item[0]] = {}
					result[item[0]]['title'] = item[1]
					result[item[0]]['price'] = item[2]
					result[item[0]]['link'] = item[3]
		else:
			result[item[0]] = {}
			result[item[0]]['title'] = item[1]
			result[item[0]]['price'] = item[2]
			result[item[0]]['link'] = item[3]
	if range_to == total_count:
		return result, True
	else:
		center('Successfully gathered page {}/{}!!'.format(str(page), str(int(math.ceil(int(total_count) / 120)))))
		smart_sleep(delay)
		page += 1
		return gather_items(query, result, range_to, page)

def send_message(item, channel, ts=None):
	attachments = [
		{
			'fallback': html.unescape(item['title']).title(),
			'color': '#36a64f',
			'title': html.unescape(item['title']).title(),
			'title_link': item['link'],
			'fields': [
				{
					'title': 'Price',
					'value': item['price'],
					'short': True
				}
			],
			'image_url': gather_image(item['link']),
			'footer': 'Powered by @DefNotAvg',
			'footer_icon': 'https://pbs.twimg.com/profile_images/1085294066303160320/D7gH8G_-_400x400.jpg',
			'ts': time()
		}
	]
	center(html.unescape(item['title']).title())
	center('Price: {}'.format(item['price']))
	if ts:
		message = sc.api_call(
			'chat.update',
			ts = ts,
			channel = channel,
			attachments = attachments
		)
	else:
		message = sc.api_call(
			'chat.postMessage',
			channel = channel,
			attachments = attachments
		)
	return message

initial = True
items = {}
sc = SlackClient(slack_token)
while True:
	header()
	i = 0
	while i < len(list(searches.keys())):
		query = list(searches.keys())[i]
		center('Search: {}'.format(query.title()))
		center('-', '-')
		if initial:
			print('{}\r'.format(center('Gathering initial items...', display=False)), end='')
			items[query], success = gather_items(query, {})
			if success:
				center('Successfully gathered initial items!!')
			else:
				center('Unable to gather items.')
			center(' ')
			smart_sleep(delay)
		else:
			print('{}\r'.format(center('Gathering new items...', display=False)), end='')
			new = {}
			gathered_items, success = gather_items(query, items[query])
			for data_id in gathered_items.keys():
				if data_id not in items[query].keys():
					new[data_id] = gathered_items[data_id]
				elif any(gathered_items[data_id][key] != items[query][data_id][key] for key in gathered_items[data_id].keys()):
					new[data_id] = gathered_items[data_id]
			if success:
				if len(list(new.keys())) == 0:
					print('{}\n'.format(center('No new items found.', display=False)))
				elif len(list(new.keys())) == 1:
					center('{} new item found!!'.format(str(len(list(new.keys())))))
				else:
					center('{} new items found!!'.format(str(len(list(new.keys())))))
			else:
				center('Unable to gather items.')
			if new:
				center(' ')
				for key in new.keys():
					try:
						message = send_message(new[key], searches[query], items[query][key]['ts'])
					except KeyError:
						message = send_message(new[key], searches[query])
					if message['ok']:
						center('Successfully sent message!!')
						items[query][key] = new[key]
						items[query][key]['ts'] = message['ts']
					else:
						center('Unable to send message.')
					center(' ')
			smart_sleep(delay)
		if i != len(list(searches.keys())) - 1:
			center('-', '-')
		if success:
			i += 1
		else:
			header()
	initial = False