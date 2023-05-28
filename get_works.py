# Retrieve fic ids from an AO3 search
# Will return in searched order
# Saves ids to a csv for later use e.g. to retrieve fic text
from bs4 import BeautifulSoup
import time, requests, csv, os
from rich.progress import track, Progress


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
	with open(args['file_name'] + ".csv", 'a', newline='', encoding='utf8') as csvfile:
		writer = csv.writer(csvfile, delimiter=',')
		for id in ids:
			if not not_finished(args): break
			writer.writerow([val for key, val in id.items()])
			args['num_gotten'] += 1
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

	works = soup.select("li.work.blurb.group")
	# see if we've gone too far and run out of fic:
	if (len(works) == 0):
		args['is_page_empty'] = True

	# process list for new fic ids
	ids = []
	for work in works:
		if args['oneshots(yes/no/only)'] == 'no' and work.find('dd', class_="chapters").text == '1/1': continue
		if args['oneshots(yes/no/only)'] == 'only' and work.find('dd', class_="chapters").text != '1/1': continue
		if args['to_get']['id'](work) in seen_ids: continue
		ids.append({key: func(work) for key, func in args['to_get'].items()})
		seen_ids.add(ids[-1]['id'])
	return ids
def not_finished(args):
	if (args['is_page_empty']):
		return False
	if (args['num_to_get'] == -1):
		return True
	else:
		if (args['num_gotten'] < args['num_to_get']):
			return True
		else:
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
def get_args(default_args, to_skip):
	# loop though all keys in args expect for last 2
	for key in list(default_args)[:to_skip * -1]:
		response = input(key + '=')
		if response:
			if default_args[key].__class__ is int:
				try: default_args[key] = int(response)
				except ValueError: print("error: should be int")
			elif default_args[key].__class__ is float:
				try: default_args[key] = float(response)
				except ValueError: print("error: should be float")
			elif key == 'oneshots(include/exclude/exclusive)':
				if response in ('inc', '1', 'include', 'yes', 'y'): default_args[key] = 'yes'
				elif response == ('2', 'exclude', 'no', 'n'): default_args[key] = 'no'
				elif response == ('3', 'exclusive', 'only', 'o'): default_args[key] = 'only'
				else: print("error: should be yes/no/only")
			else:
				default_args[key] = response
	return default_args
def main():
	args = {
		'url': None,
		'delay': 5.0,
		'num_to_get': -1,
		'file_name': 'work_ids',
		'header': '',
		'oneshots(yes/no/only)': 'yes',
		'num_gotten': 0,
		'is_page_empty': False,
		'to_get': {
			'id': lambda w: w.get('id')[5:],
			'kudos': lambda w: w.find('dd', class_="kudos").text,
			'hits': lambda w: w.find('dd', class_="hits").text,
			'body': lambda w: str(w).replace('\n', '').replace('\r', '').replace('\t', '').replace('href="/', 'href="https://archiveofourown.org/')
		}
	}
	get_args(args, 3)
	seen = load_existing_ids(args)
	with Progress() as progress:
		progress.add_task('processing: ', total=args['num_to_get'] // 20 + 1)
		while not_finished(args):
			write_ids_to_csv(args, get_ids(args, seen))
			update_url_to_next_page(args)
			time.sleep(args['delay'])
			progress.update(0, advance=1)


if __name__ == "__main__":
	main()
