from __future__ import print_function
import requests
import json
import os
import math
import re
import html
from time import sleep, time
from slackclient import SlackClient

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
	except requests.exceptions.ConnectionError:
		return ''
	return content.split('<img src="')[1].split('"')[0]

def gather_items(query, items):
	result = dict(items)
	links = []
	params = (
		('query', query),
		('search_distance', distance),
		('postal', zip_code),
	)
	if max_price:
		params += ('max_price', max_price)
	try:
		response = requests.get('https://{}.craigslist.org/search/sss'.format(location), headers=headers, params=params)
		content = response.content.decode('utf-8')
	except requests.exceptions.ConnectionError:
		return result, False
	range_to = content.split('<span class="rangeTo">')[1].split('</span>')[0]
	total_count = content.split('<span class="totalcount">')[1].split('</span>')[0]
	titles = re.findall(r'class="result-title hdrlnk">(.*?)</a>', content)
	data_ids = re.findall(r'data-id="(.*?)"', content)
	for data_id in data_ids:
		links.append('https://{}.craigslist.org/{}/{}.html'.format(location, content.split(data_id)[-4].split('craigslist.org/')[-1].split('/')[0], data_id))
	prices = re.findall(r'<span class="result-price">(.*?)</span>', content)
	for item in zip(data_ids, titles, prices, links):
		result[item[0]] = {}
		result[item[0]]['title'] = item[1]
		result[item[0]]['price'] = item[2]
		result[item[0]]['link'] = item[3]
	return result, True

def send_message(item, channel):
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
			'footer': 'Powered by @DefNotAvg',
			'footer_icon': 'https://pbs.twimg.com/profile_images/1085294066303160320/D7gH8G_-_400x400.jpg',
			'ts': time()
		}
	]
	image = gather_image(item['link'])
	if image:
		attachments[0]['image_url'] = image
	center(html.unescape(item['title']).title())
	center('Price: {}'.format(item['price']))
	message = sc.api_call(
		'chat.postMessage',
		channel = channel,
		attachments = attachments
	)
	if message['ok']:
		center('Successfully sent message!!')
	else:
		center('Unable to send message.')

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
				elif gathered_items[data_id] != items[query][data_id]:
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
					send_message(new[key], searches[query])
					center(' ')
			smart_sleep(delay)
			items[query] = gathered_items
		if i != len(list(searches.keys())) - 1:
			center('-', '-')
		if success:
			i += 1
		else:
			header()
	initial = False