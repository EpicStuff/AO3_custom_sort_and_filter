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
def load_csv(file, col=-1, create=False, to_write=[]):
	import os, csv
	from rich.progress import track
	file = file + '.csv'; lines = []
	# if file exists and is not empty
	if (os.path.exists(file)) and os.stat(file).st_size:
		with open(file, 'r', newline='', encoding='utf8') as f:
			reader = csv.reader(f, delimiter=',')
			# get number of columns in csv
			csv_len = len(next(reader))
			for row in track(reader, 'loading file: ', sum(1 for line in open(file, 'rbU')) - 1):
				# if there are commas in the last column, join them
				if len(row) > csv_len:
					row = row[:csv_len - 1] + [','.join(row[csv_len - 1:])]
				if col < 0:
					lines.append(row)
				else:
					lines.append(row[col])
	elif create:
		print("no existing file; creating new file...\n")
		with open(file, 'w', newline='', encoding='utf8') as f:
			writer = csv.writer(f, delimiter=',')
			writer.writerow(to_write)
	return lines
