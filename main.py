from flask import Flask, render_template
import os

app = Flask(__name__, template_folder='outputs', static_folder='outputs/ao3_template')

@app.route("/")
def main():
	html = ''
	files = os.listdir('outputs')
	files.sort()
	for file in files:
		if file.endswith('.html'):
			html += f'<a href="{file}">{file}</a><br>'
	# return render_template('alex_rider_1.html')
	return html


@app.route('/<file>')
def page(file):
	print(file)
	return render_template(file)


app.run(host='0.0.0.0')
