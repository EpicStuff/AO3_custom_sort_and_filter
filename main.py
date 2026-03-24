from pathlib import Path

from flask import Flask, render_template

app = Flask(__name__, template_folder='outputs', static_folder='outputs/ao3_template')

@app.route('/')
def main() -> str:
	html = ''
	files = Path('outputs').iterdir()
	for file in sorted(files):
		if file.suffix == '.html':
			html += f'<a href="{file}">{file}</a><br>'
	return html


@app.route('/<file>')
def page(file):
	print(file)
	return render_template(file)


app.run(host='127.0.0.1')
