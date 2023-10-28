import os
from bs4 import BeautifulSoup
from rich.progress import track
from stuff import *


def main():
	args = {
		'in_file': None,
		'sort_by': 'ratio',
		'min':
		{
			'hits': 100,
			'words': 2000,
		},
		'out_file': None,
		'works_to_skip': 'bookmarks',
		'out_folder': 'outputs/',
		'works_per_page': 20,
		'template': 'ao3_template',
		'to_get':
		{
			'words': lambda soup: int(soup.find('dd', class_="words").text.replace(',', '')),
			'kudos': lambda soup: int(soup.find('dd', class_="kudos").text.replace(',', '')),
			'hits': lambda soup: int(soup.find('dd', class_="hits").text.replace(',', '')),
		},
		'sort':
		{
			'ratio': lambda work: work[2]['kudos'] / work[2]['hits'],
			'ratio modified': lambda work: work[2]['kudos'] / (work[2]['hits'] + args['min_hits']),
			'kudos': lambda work: work[2]['kudos'],
		},
	}
	# load args
	args = get_args(args, 3)
	# if no out_file specified, use in_file
	if not args['out_file']:
		args['out_file'] = args['in_file']

	# load works
	works = load_csv(args['in_file'])
	# load works to skip and skip
	if args['works_to_skip']:
		try:
			works_to_skip = {*load_csv(args['works_to_skip'], 0)}
			works = [work for work in works if not work[0] in works_to_skip]
		except FileNotFoundError as e:
			print('skipping skipping:', e)

	# extract data
	for work in track(works.copy(), 'processing works:', len(works)):
		work.append({})
		soup = BeautifulSoup(work[1], 'lxml')
		try: args['to_get']['kudos'](soup)  # if works does not have kudos (is probably a series)
		except AttributeError: continue  # skip work
		for key, func in args['to_get'].items():
			work[2][key] = func(soup)

	# skip works with no stats
	works = [work for work in works if work[2] != {}]
	# skip works with less that min_hits
	if args['min']['hits'] > 0:
		works = [work for work in works if work[2]['hits'] >= args['min']['hits']]
	if args['min']['words'] > 0:
		works = [work for work in works if work[2]['words'] >= args['min']['words']]

	# sort works
	works.sort(key=args['sort'][args['sort_by']], reverse=True)

	# split works into pages
	works = [works[i:i + args['works_per_page']] for i in range(0, len(works), args['works_per_page'])]

	if args['out_folder']:
		os.makedirs(args["out_folder"], exist_ok=True)
		args['out_file'] = args['out_folder'] + args['out_file']
	for current_page, page in track(enumerate(works), 'processing files:', len(works)):
		# load template
		with open(args['template'] + '.html', 'r', encoding='utf8') as f:
			soup = BeautifulSoup(f, 'lxml')

		soup.find('h2', class_='heading').string = f"{current_page * args['works_per_page'] + 1} - {(current_page + 1) * args['works_per_page'] if (current_page + 1) * args['works_per_page'] < len(sum(works, [])) else len(sum(works, []))} of {len(sum(works, []))} Works"

		# for bar at top and bottom of page
		for navigation in soup.find_all('ol', class_='pagination actions'):
			# add prev
			if not current_page == 0:
				navigation.append(BeautifulSoup(f'<li class="previous" title="previous"><a rel="prev" href="{args["out_file"].split("/")[-1]}_{current_page}.html">← Previous</a></li>', 'lxml'))
			# add page number buttons
			for page_num in range(len(works)):
				if page_num == current_page:
					navigation.append(BeautifulSoup(f'<li><span class="current">{str(current_page + 1)}</span></li>', 'lxml'))
				elif page_num in (0, 1) or page_num in (len(works) - 2, len(works) - 1) or page_num in range(current_page - 4, current_page + 4):
					navigation.append(BeautifulSoup(f'<li><a href="{args["out_file"].split("/")[-1]}_{str(page_num + 1)}.html">{str(page_num + 1)}</a></li>', 'lxml'))
				elif page_num in (current_page - 5, current_page + 5):
					navigation.append(BeautifulSoup('<li class="gap">…</li>', 'lxml'))
			# add next
			if not current_page == len(works) - 1:
				navigation.append(BeautifulSoup(f'<li class="next" title="next"><a rel="next" href="{args["out_file"].split("/")[-1]}_{current_page + 2}.html">Next →</a></li>', 'lxml'))

		# add works to page
		for work in page:
			soup.find('ol', class_='work index group').append(BeautifulSoup(work[1], 'lxml'))

		# save page
		with open(f'{args["out_file"]}_{str(current_page + 1)}.html', 'w', encoding='utf8') as f:
			f.write(soup.prettify())


if __name__ == "__main__":
	main()
