# Craigslist Monitor

A simple program to monitor new items on Craigslist.

## Getting Started

Edit config.json to your liking then run main.py.

## config.json

* location - Your craigslist location (AKA the part that comes before craigslist.org)
* searches - A dictionary of queries with the matching Slack channel alerts should be sent to
* zipCode - Zip code used to search for items
* distance - Number of miles to create a search radius around the above zip code
* maxPrice - Maximum price (leave blank to disregard this parameter)
* delay - Number of seconds to sleep in between each cycle
* width - Number of characters to center the program output around
* slackToken - Token used to send messages in Slack

## Prerequisites

* Currently working on Python 3.7.3
* [requests](http://docs.python-requests.org/en/master/)
* [slackclient](https://python-slackclient.readthedocs.io/en/latest/)

## To-Do

- [x] Add support for searches with multiple pages of results
- [ ] Allow parameters such as maxPrice to be set for each query
- [ ] Add support for more support parameters
- [ ] Update README with examples