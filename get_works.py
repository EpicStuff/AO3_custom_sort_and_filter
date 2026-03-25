'''get_works.py.

Save fic ids (and optionally html) from AO3 to a csv file.

Usage:
	get_works [options] <url>
	get_works -h, --help
	get_works --version

Options:
	-h, --help                  Show this.
	--version                   Show version.

	-o, --output <output>       File to save works to.
	-i, --input [<input>]       File to merge new works with.
	-I                          Use same input file as output file. Do not use -i with this flag.

	-w, --works-to-get <works>  Number of works to get. Defaults to all.
	-p, --pages-to-get <pages>  Number of pages to get. Defaults to all.

	-s, --skip <skip>           File containing works to skip.
	-d, --delay <delay>         Delay between requests in seconds. [Default: 5]
	--id-only                   Only save the id of each work, not the html.
'''
import csv, time
from pathlib import Path
from functools import cache

import requests
from bs4 import BeautifulSoup
from docopt import docopt
from epicstuff import Dict, Bar
from rich.progress import TextColumn
from stuff import load_csv


@cache
def get_request(url: str) -> requests.Response:
	return requests.get(url, timeout=60)

def update_url_to_next_page(args: Dict) -> None:
	key = 'page='
	start = args.url.find(key)

	# there is already a page indicator in the url
	if start != -1:
		# find where in the url the page indicator starts and ends
		page_start_index = start + len(key)
		page_end_index = args.url.find('&', page_start_index)
		# if it's in the middle of the url
		if page_end_index != -1:
			page = int(args.url[page_start_index:page_end_index]) + 1
			args.url = args.url[:page_start_index] + str(page) + args.url[page_end_index:]
		# if it's at the end of the url
		else:
			page = int(args.url[page_start_index:]) + 1
			args.url = args.url[:page_start_index] + str(page)

	# there is no page indicator, so we are on page 1
	# there are other modifiers
	elif (args.url.find('?') != -1):
		args.url += '&page=2'
	# there an no modifiers yet
	else:
		args.url += '?page=2'
def write_ids_to_csv(args: Dict, stuff: Dict, ids: list[dict]) -> None:
	with args.output.open('a', newline='', encoding='utf8') as f:
		writer = csv.writer(f, delimiter=',')
		for id_ in ids:
			if is_done(args, stuff): break
			writer.writerow([val for _, val in id_.items()])
			stuff.works_gotten += 1
	stuff.pages_gotten += 1
def get_ids(args: Dict, stuff: Dict, seen_ids: set[str]) -> list[dict]:
	# make the request. if we 429, try again later
	req = get_request(args.url)
	while req.status_code == 429:
		time.sleep(args.delay)
		req = requests.get(args.url)
		print('Request answered with Status-Code 429, retrying...')

	soup = BeautifulSoup(req.text, 'lxml')

	works = soup.select('li.blurb.group')
	# see if we've gone too far and run out of fic:
	if len(works) == 0:
		stuff.is_page_empty = True

	# process list for new fic ids
	ids = []
	for work in works:
		# if args['to_get']['id'](work) in seen_ids: continue
		try:
			work = {key: func(work) for key, func in stuff.to_get.items()}
		except AttributeError:  # made for if bookmarked wark has been deleted
			assert work.find('p', class_='message').contents[0] == 'This has been deleted, sorry!'  # making sure its not some other problem  # pyright: ignore[reportOptionalMemberAccess]
			continue
		if work['id'] not in seen_ids:
			if args.id_only:
				ids.append({'id': work['id']})
			else:
				ids.append(work)
			seen_ids.add(ids[-1]['id'])
	return ids
def is_done(args: Dict, stuff: Dict) -> bool:
	return \
		stuff.is_page_empty or \
		(args.works_to_get > 0 and stuff.works_gotten >= args.works_to_get) or \
		(args.pages_to_get > 0 and stuff.pages_gotten >= args.pages_to_get)
def create_file(file: Path, to_write: list[str]) -> None:
	print('creating/overwriting file\n')
	with file.open('w', newline='', encoding='utf8') as f:
		writer = csv.writer(f, delimiter=',')
		writer.writerow(to_write)
def main() -> None:  # noqa: C901, PLR0912
	stuff = Dict({
		'works_gotten': 0,
		'pages_gotten': 0,
		'is_page_empty': False,
		'to_get': {
			'id': lambda w: w.find('h4', class_='heading').find('a').get('href').split('/')[-1],
			'body': lambda w: str(w).replace('\n', '').replace('\r', '').replace('\t', '').replace('href="/', 'href="https://archiveofourown.org/'),
		},
	})
	# get args
	args = Dict({key.lstrip('-').replace('-', '_').lstrip('<').rstrip('>'): val for key, val in docopt(__doc__).items()}, _convert=True)  # pyright: ignore[reportArgumentType]
	# process args
	if args.input and args.I:
		raise ValueError('Cannot use -i and -I together.')
	if args.I:
		args.input = args.output
	args.output = Path(args.output)
	if not args.output.suffix:
		args.output = args.output.with_suffix('.csv')
	args.works_to_get = int(args.works_to_get) if args.works_to_get else -1
	args.pages_to_get = int(args.pages_to_get) if args.pages_to_get else -1
	args.delay = int(args.delay)

	# load existing ids
	seen = {*load_csv(args.input, 0)} if args.input else set()
	# load existing ids from skip file
	if args.skip:
		seen.update(load_csv(args.skip, 0))

	# create out file if necessary (doesn't exist, is empty, or input is none)
	if args.input is None or not args.output.exists() or not args.output.stat().st_size:
		create_file(args.output, list(stuff.to_get))

	# scrape ao3 with progress bars
	# bar1 is for main bar with MofN, bar2 is for sub bars without MofN
	Bar1 = Bar()
	with Bar1 as bar1, Bar(add_columns={0: TextColumn('\t')}, remove_columns=[1]) as bar2:
		# get total number of pages/works
		tmp_bar = bar2(range(1), 'Working', None, True)
		next(tmp_bar)
		req = get_request(args.url)
		req.raise_for_status()
		soup = BeautifulSoup(req.text, 'lxml')
		soup = soup.find('ol', class_='pagination').find_all('li')  # pyright: ignore[reportOptionalMemberAccess]
		if soup[-1].get('class') == ['next']:
			del soup[-1]
		pages = int(soup[-1].find('a').text)  # pyright: ignore[reportOptionalMemberAccess]

		soup = BeautifulSoup(req.text, 'lxml').find('h2', class_='heading')
		works = int(soup.text.split()[4].replace(',', ''))  # pyright: ignore[reportOptionalMemberAccess]

		next(tmp_bar, None)

		# determine if pages or works is the stopping factor, assumes 20 works per page
		if args.works_to_get > 0 and args.pages_to_get > 0:
			limit = 'pages' if args.pages_to_get * 20 < args.works_to_get else 'works'
		elif args.works_to_get < 0 and args.pages_to_get < 0:
			limit = 'pages'
		else:
			limit = 'pages' if args.pages_to_get > 0 else 'works'

		if limit == 'pages':
			main_bar = bar1(range(min(pages, args.pages_to_get) if args.pages_to_get > 0 else pages), 'Page:', cycle=False)
		else:
			main_bar = bar1(range(min(works, args.works_to_get) if args.works_to_get > 0 else works), 'Work:', cycle=False)
		next(main_bar)

		# loop until reached specified number of pages/works or all works have been gotten
		while True:
			# actual scraping
			request_bar = bar2(range(1), 'Requesting page', None, True)
			next(request_bar)
			write_ids_to_csv(args, stuff, get_ids(args, stuff, seen))
			update_url_to_next_page(args)
			next(request_bar, None)

			# more progress bar stuff
			if limit == 'pages':
				next(main_bar, None)
			else:
				Bar1.progress.update(Bar1.tasks[0], completed=stuff.works_gotten) # pyright: ignore[reportOptionalMemberAccess]

			if is_done(args, stuff):
				break
			# else:
			steps = 100
			for _ in bar2(range(steps), 'Sleeping', transient=True):
				time.sleep(args.delay / steps)

		#next(main_bar, None)


if __name__ == '__main__':
	main()
