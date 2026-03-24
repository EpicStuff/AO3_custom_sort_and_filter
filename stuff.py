import csv
from pathlib import Path


def load_csv(file: str, col: int = -1) -> list[str]:  # pyright: ignore[reportRedeclaration]
	lines = []
	file: Path = Path(file)
	if not file.suffix:
		file = file.with_suffix('.csv')
	# if file exists and is not empty
	if file.exists() and file.stat().st_size:
		with file.open(newline='', encoding='utf8') as f:
			reader = csv.reader(f, delimiter=',')
			# get number of columns in csv
			csv_len = len(next(reader))
			for row in reader:
				# if there are commas in the last column, join them
				if len(row) > csv_len:
					row = [*row[:csv_len - 1], ','.join(row[csv_len - 1:])]
				if col < 0:
					lines.append(row)
				else:
					lines.append(row[col])
		return lines
	raise FileNotFoundError(f'file not found: {file}')
