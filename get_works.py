# Retrieve fic ids from an AO3 search
# Will return in searched order
# Saves ids to a csv for later use e.g. to retrieve fic text
from bs4 import BeautifulSoup
import time, requests, csv, os
from rich.progress import track, Progress
from stuff import *


def update_url_to_next_page(args):
	key = "page="
	start = args['url'].find(key)

	# there is already a page indicator in the url
	if (start != -1):
		# find where in the url the page indicator starts and ends
		page_start_index = start + len(key)
		page_end_index = args['url'].find("&", page_start_index)
		# if it's in the middle of the url
		if (page_end_index != -1):
			page = int(args['url'][page_start_index:page_end_index]) + 1
			args['url'] = args['url'][:page_start_index] + str(page) + args['url'][page_end_index:]
		# if it's at the end of the url
		else:
			page = int(args['url'][page_start_index:]) + 1
			args['url'] = args['url'][:page_start_index] + str(page)

	# there is no page indicator, so we are on page 1
	else:
		# there are other modifiers
		if (args['url'].find("?") != -1):
			args['url'] += "&page=2"
		# there an no modifiers yet
		else:
			args['url'] += "?page=2"
def write_ids_to_csv(args, ids):
	with open(args['file_out'] + '.csv', 'a', newline='', encoding='utf8') as f:
		writer = csv.writer(f, delimiter=',')
		for id in ids:
			if is_done(args): break
			writer.writerow([val for key, val in id.items()])
			args['num_gotten'] += 1
	args['pages_gotten'] += 1
def get_ids(args, seen_ids):
	# make the request. if we 429, try again later
	headers = {'user-agent': args['header']}
	req = requests.get(args['url'], headers=headers)
	while req.status_code == 429:
		# >5 second delay between requests as per AO3's terms of service
		time.sleep(max(args['delay'], 5))
		req = requests.get(args['url'], headers=headers)
		print("Request answered with Status-Code 429, retrying...")

	soup = BeautifulSoup(req.text, "lxml")

	works = soup.select("li.blurb.group")
	# see if we've gone too far and run out of fic:
	if (len(works) == 0):
		args['is_page_empty'] = True

	# process list for new fic ids
	ids = []
	for work in works:
		# if args['oneshots(yes/no/only)'] == 'no' and work.find('dd', class_="chapters").text == '1/1': continue
		# if args['oneshots(yes/no/only)'] == 'only' and work.find('dd', class_="chapters").text != '1/1': continue
		# if args['to_get']['id'](work) in seen_ids: continue
		work = {key: func(work) for key, func in args['to_get'].items()}
		if work['id'] not in seen_ids:
			ids.append(work)
			seen_ids.add(ids[-1]['id'])
	return ids
def is_done(args):
	if args['is_page_empty']:
		return True
	if args['num_to_get'] > 0 and args['num_gotten'] >= args['num_to_get']:
		return True
	if args['pages_to_get'] > 0 and args['pages_gotten'] >= args['pages_to_get']:
		return True
	return False
def load_existing_ids(args, ids=set()):
	if (os.path.exists(args['file_name'] + '.csv')) and os.stat(args['file_name'] + '.csv').st_size:
		with open(args['file_name'] + ".csv", 'r', encoding='utf8') as f:
			reader = csv.reader(f)
			for row in track(reader, 'loading file: ', sum(1 for line in open(args['file_name'] + '.csv', 'rbU'))):
				ids.add(row[0])
	else:
		print("no existing file; creating new file...\n")
		with open(args['file_name'] + '.csv', 'w', newline='', encoding='utf8') as f:
			writer = csv.writer(f, delimiter=',')
			writer.writerow(list(args['to_get']))
	return ids
def create_file(file, to_write):
	print("no existing file; creating new file...\n")
	with open(file + '.csv', 'w', newline='', encoding='utf8') as f:
		writer = csv.writer(f, delimiter=',')
		writer.writerow(to_write)
def main():
	args = {
		'url': None,
		'delay': 5.0,
		'num_to_get': -1,
		'pages_to_get': -1,
		'file_in': None,
		'file_out': 'work_ids',
		'header': '',
		# 'oneshots(yes/no/only)': 'yes',
		'num_gotten': 0,
		'pages_gotten': 0,
		'is_page_empty': False,
		'to_get': {
			'id': lambda w: w.find('h4', class_="heading").find('a').get('href').split('/')[-1],
			'body': lambda w: str(w).replace('\n', '').replace('\r', '').replace('\t', '').replace('href="/', 'href="https://archiveofourown.org/')
		}
	}
	# get user args
	args = get_args(args, 4)
	# load existing ids
	try:
		seen = {*load_csv(args['file_in'], 0)}
	except FileNotFoundError as e:
		print(e)
		seen = set()
		if args['file_in'] == args['file_out']:
			create_file(args['file_out'], list(args['to_get']))
	# create file if necessary
	if args['file_in'] != args['file_out']:
		create_file(args['file_out'], list(args['to_get']))

	with Progress() as progress:
		bars = {}
		if args['num_to_get'] > 0:
			bars['num'] = [progress.add_task('works gotten: ', total=args['num_to_get']), 0]
		if args['pages_to_get'] > 0:
			bars['pages'] = [progress.add_task('pages processed: ', total=args['pages_to_get'], ), 0]
		elif not args['num_to_get'] > 0:
			progress.add_task('processing: ', total=None)
		while not is_done(args):
			write_ids_to_csv(args, get_ids(args, seen))
			update_url_to_next_page(args)

			if 'num' in bars:
				bars['num'][1] = args['num_gotten'] - progress.tasks[bars['num'][0]].completed
			if 'pages' in bars:
				bars['pages'][1] = args['pages_gotten'] - progress.tasks[bars['pages'][0]].completed

			steps = 100
			for i in range(steps):
				if 'num' in bars:
					progress.update(bars['num'][0], advance=bars['num'][1] / steps)
				if 'pages' in bars:
					progress.update(bars['pages'][0], advance=bars['pages'][1] / steps)
				time.sleep(args['delay'] / steps)


if __name__ == "__main__":
	main()
