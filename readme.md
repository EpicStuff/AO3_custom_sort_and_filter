# AO3Scraper

Based off of [AO3Scraper](https://github.com/radiolarian/AO3Scraper)

Features:
- Given a fandom or collection URL and amount of works you want, returns a list of the fic IDs and its html
- Sorts list of works by whatever, optionally filter out works in another list (say your bookmarked works)
- Exports works to html files

## Dependencies
- pip install bs4
- pip install requests
- pip install lxml


## Example Usage

Let's say you wanted to collect data from the first 100 English completed fics, ordered by kudos, in the Sherlock (TV) fandom. The first thing to do is use AO3's nice search feature on their website.

We get this URL as a result: http://archiveofourown.org/works?utf8=%E2%9C%93&work_search%5Bsort_column%5D=kudos_count&work_search%5Bother_tag_names%5D=&work_search%5Bquery%5D=&work_search%5Blanguage_id%5D=1&work_search%5Bcomplete%5D=0&work_search%5Bcomplete%5D=1&commit=Sort+and+Filter&tag_id=Sherlock+%28TV%29 

Run `get_works.py`. You can optionally add some flags: 
- enter args when prompted
- enter to skip to default to default args

The only required input is the search URL.  

For our example, we might say: 

Now, to actually get the works, run `process_works`. 

## License
just don't copy and stuff