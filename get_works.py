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

	-n, --num-to-get <num>      Number of works to get. Defaults to all.
	-p, --pages-to-get <pages>  Number of pages to get. Defaults to all.

	-s, --skip <skip>           File containing works to skip.
	-d, --delay <delay>         Delay between requests in seconds. [Default: 5]
	--id-only                   Only save the id of each work, not the html.
'''
import csv, time
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from docopt import docopt
from epicstuff import Dict
from rich.progress import Progress
from stuff import load_csv


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
			stuff.num_gotten += 1
	stuff.pages_gotten += 1
def get_ids(args: Dict, stuff: Dict, seen_ids: set[str]) -> list[dict]:
	# make the request. if we 429, try again later
	req = requests.get(args.url)
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
		(args.num_to_get > 0 and stuff.num_gotten >= args.num_to_get) or \
		(args.pages_to_get > 0 and stuff.pages_gotten >= args.pages_to_get)
def create_file(file: Path, to_write: list[str]) -> None:
	print('no existing file; creating new file...\n')
	with file.open('w', newline='', encoding='utf8') as f:
		writer = csv.writer(f, delimiter=',')
		writer.writerow(to_write)
def main() -> None:  # noqa: C901, PLR0912
	stuff = Dict({
		'num_gotten': 0,
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
	args.num_to_get = int(args.num_to_get) if args.num_to_get else -1
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

	with Progress() as progress:
		bars = {}
		if args.num_to_get > 0:
			bars['num'] = [progress.add_task('works gotten: ', total=args.num_to_get), 0]
		if args.pages_to_get > 0:
			bars['pages'] = [progress.add_task('pages processed: ', total=args.pages_to_get), 0]
		elif not args.num_to_get > 0:
			progress.add_task('processing: ', total=None)
		while not is_done(args, stuff):
			write_ids_to_csv(args, stuff, get_ids(args, stuff, seen))
			update_url_to_next_page(args)

			if 'num' in bars:
				bars['num'][1] = stuff.num_gotten - progress.tasks[bars['num'][0]].completed
			if 'pages' in bars:
				bars['pages'][1] = stuff.pages_gotten - progress.tasks[bars['pages'][0]].completed

			steps = 100
			for _ in range(steps):
				if 'num' in bars:
					progress.update(bars['num'][0], advance=bars['num'][1] / steps)
				if 'pages' in bars:
					progress.update(bars['pages'][0], advance=bars['pages'][1] / steps)
				time.sleep(args['delay'] / steps)


if __name__ == '__main__':
	main()
