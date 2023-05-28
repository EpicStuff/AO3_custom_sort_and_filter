import csv, os
from bs4 import BeautifulSoup
from rich.progress import track

def get_args(default_args):
	# loop though all keys in args expect for last 2
	for key in list(default_args):
		response = input(key + '=')
		if response:
			if default_args[key].__class__ is int:
				try: default_args[key] = int(response)
				except ValueError: print("error: should be int")
			# elif args[key].__class__ is float:
			# 	try: args[key] = float(response)
			# 	except ValueError: print("error: should be float")
			else:
				default_args[key] = response
	return default_args
def main():
	args = {'in_file': 'work_ids', 'out_file': 'outputs/works_sorted', 'sort_by': 'ratio', 'template': 'ao3_template', 'works_per_page': 20, 'works_to_skip': 'bookmarks', 'min_hits': 100}
	get_args(args)

	# load works
	works = []
	with open(args['in_file'] + '.csv', 'r', newline='', encoding='utf8') as f:
		reader = csv.reader(f, delimiter=',')
		csv_len = len(next(reader))
		for row in reader:
			if len(row) > csv_len:
				row = row[:csv_len - 1] + [','.join(row[csv_len - 1:])]
			works.append(row)

	# load works to skip and skip
	try:
		with open(args['works_to_skip'] + '.csv', 'r', newline='', encoding='utf8') as f:
			reader = csv.reader(f, delimiter=',')
			work_to_skip = [row[0].split('/')[-1] for row in reader]
		# remove all works in works to skip from works
		works = [work for work in works if not work[0] in work_to_skip]
	except Exception as e: print('skipping skipping:', e)
	# skip works with less that min_hits
	if args['min_hits'] > 0:
		works = [work for work in works if int(work[2]) >= args['min_hits']]

	if args['sort_by'] == 'ratio':
		works.sort(key=lambda x: float(x[1]) / float(x[2]), reverse=True)
	elif args['sort_by'] == 'ratio modified':
		works.sort(key=lambda x: (float(x[1]) + 0) / (float(x[2]) + 10), reverse=True)

	# split works into pages
	works = [works[i:i + args['works_per_page']] for i in range(0, len(works), args['works_per_page'])]

	for current_page, page in track(enumerate(works), '', len(works)):
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
			soup.find('ol', class_='work index group').append(BeautifulSoup(work[-1], 'lxml'))

		# save page
		try:
			os.makedirs(os.path.dirname(args["out_file"]), exist_ok=True)
		except FileNotFoundError as e: print(e)
		with open(f'{args["out_file"]}_{str(current_page + 1)}.html', 'w', encoding='utf8') as f:
			f.write(soup.prettify())


if __name__ == "__main__":
	main()
