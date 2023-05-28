def get_args(default_args, to_skip):
	def format_response(response, type):
		try:
			if type is int:
				return int(response)
			if type is float:
				return float(response)
			if key == 'oneshots(include/exclude/exclusive)':
				if response in {'inc', '1', 'include', 'yes', 'y'}:
					return 'yes'
				elif response in {'2', 'exclude', 'no', 'n'}:
					return 'no'
				elif response in {'3', 'exclusive', 'only', 'o'}:
					return 'only'
				else:
					print("error: should be yes/no/only")
			return response
		except ValueError:
			print('error: should be', type)

	while True:
		args = default_args.copy()
		try:
			# loop though all keys in args expect for last `to_skip`
			for key in list(args)[:to_skip * -1]:
				if args[key].__class__ is dict:
					for sub_key, sub_arg in args[key].items():
						response = input(f'{key}.{sub_key}=')
						if response:
							args[key][sub_key] = format_response(response, sub_arg.__class__)
				else:
					response = input(key + '=')
					if response:
						args[key] = format_response(response, args[key].__class__)
			return args
		except KeyboardInterrupt:
			print('\nrestarting...\n')
def load_csv(file, col=-1):
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
		return lines
	return FileNotFoundError(f'file not found: {file}')
