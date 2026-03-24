'''process_works.py.

Process works from a csv file into HTML.

Usage:
	process_works [options] <input> [<output>]
	process_works -h, --help
	process_works --version

Options:
	-h, --help                    Show this.
	--version                     Show version.

	-o, --out-folder <folder>  Folder to save works to. [Default: outputs/]

	-s, --skip <skip>             File containing works to skip.
	-S, --sort <sort>             How to sort works. [Default: ratio]
	-W, --works-per-page <num>    Number of works to show per page. [Default: 20]
	-t, --template <template>     HTML template to use. [Default: ao3_template]

	-H, --min-hits <hits>         Minimum number of hits for a work to be included. [Default: 100]
	-w, --min-words <words>       Minimum number of words for a work to be included. [Default: 2000]

'''
import os, shutil
from pathlib import Path

from bs4 import BeautifulSoup
from docopt import docopt
from epicstuff import Dict, open  # noqa: A004
from rich.progress import track
from stuff import load_csv


def main() -> None:
	stuff = Dict({
		'to_get':
		{
			'words': lambda soup: int(soup.find('dd', class_='words').text.replace(',', '')),
			'kudos': lambda soup: int(soup.find('dd', class_='kudos').text.replace(',', '')),
			'hits': lambda soup: int(soup.find('dd', class_='hits').text.replace(',', '')),
		},
		'sort':
		{
			'ratio': lambda work: work[2]['kudos'] / work[2]['hits'],
			'ratio modified': lambda work: work[2]['kudos'] / (work[2]['hits'] + args['min_hits']),
			'kudos': lambda work: work[2]['kudos'],
		},
	})
	# load args
	args = Dict({key.lstrip('-').replace('-', '_').lstrip('<').rstrip('>'): val for key, val in docopt(__doc__).items()}, _convert=True)  # pyright: ignore[reportArgumentType]
	# process args
	## if no out_file specified, use in_file
	if not args.output:
		args.output = args.input
	## convert
	args.output = Path(args.output)
	if args.output.suffix:
		args.output = args.output.with_suffix('')
	args.out_folder = Path(args.out_folder)
	args.template = Path(args.template)
	if not args.template.suffix:
		args.template = args.template.with_suffix('.html')
	args.works_per_page = int(args.works_per_page)
	args.min_hits = int(args.min_hits)
	args.min_words = int(args.min_words)

	# load works
	works = load_csv(args.input)
	# load works to skip and skip
	if args.skip:
		works_to_skip = {*load_csv(args.skip, 0)}
		works = [work for work in works if work[0] not in works_to_skip]

	# extract data
	for work in track(works.copy(), 'processing works:', len(works)):
		work.append({})
		soup = BeautifulSoup(work[1], 'lxml')
		try: stuff.to_get.kudos(soup)  # if works does not have kudos (is probably a series)
		except AttributeError: continue  # skip work
		for key, func in stuff.to_get.items():
			work[2][key] = func(soup)

	# skip works with no stats
	works = [work for work in works if work[2] != {}]
	# skip works with less that min_hits
	if args.min_hits > 0:
		works = [work for work in works if work[2]['hits'] >= args.min_hits]
	if args.min_words > 0:
		works = [work for work in works if work[2]['words'] >= args.min_words]

	# sort works
	works.sort(key=stuff.sort[args.sort], reverse=True)

	# split works into pages
	works = [works[i:i + args.works_per_page] for i in range(0, len(works), args.works_per_page)]

	if args.out_folder:
		args.out_folder.mkdir(exist_ok=True)
		args.output = args.out_folder / args.output
	for current_page, page in track(enumerate(works), 'processing files:', len(works)):
		# load template
		with args.template.open(encoding='utf8') as f:
			soup = BeautifulSoup(f, 'lxml')

		soup.find('h2', class_='heading').string = f'{current_page * args.works_per_page + 1} - {(current_page + 1) * args.works_per_page if (current_page + 1) * args.works_per_page < len(sum(works, [])) else len(sum(works, []))} of {len(sum(works, []))} Works' # pyright: ignore[reportOptionalMemberAccess]

		# for bar at top and bottom of page
		for navigation in soup.find_all('ol', class_='pagination actions'):
			# add prev
			if current_page != 0:
				navigation.append(BeautifulSoup(f'<li class="previous" title="previous"><a rel="prev" href="{args.output}_{current_page}.html">← Previous</a></li>', 'lxml'))
			# add page number buttons
			for page_num in range(len(works)):
				if page_num == current_page:
					navigation.append(BeautifulSoup(f'<li><span class="current">{current_page + 1}</span></li>', 'lxml'))
				elif page_num in (0, 1) or page_num in (len(works) - 2, len(works) - 1) or page_num in range(current_page - 4, current_page + 4):
					navigation.append(BeautifulSoup(f'<li><a href="{args.output}_{page_num + 1}.html">{page_num + 1}</a></li>', 'lxml'))
				elif page_num in (current_page - 5, current_page + 5):
					navigation.append(BeautifulSoup('<li class="gap">…</li>', 'lxml'))
			# add next
			if current_page != len(works) - 1:
				navigation.append(BeautifulSoup(f'<li class="next" title="next"><a rel="next" href="{args.output}_{current_page + 2}.html">Next →</a></li>', 'lxml'))

		# add works to page
		for work in page:
			soup.find('ol', class_='work index group').append(BeautifulSoup(work[1], 'lxml'))  # pyright: ignore[reportOptionalMemberAccess]

		# save page
		with open(f'{args.output}_{current_page + 1}.html', 'w') as f:
			f.write(soup.prettify())
	# copy template to output folder
	if args.out_folder and not (args.out_folder / args.template.stem).exists():
		shutil.copytree(args.template.with_suffix(''), args.out_folder / args.template.stem)


if __name__ == '__main__':
	main()
