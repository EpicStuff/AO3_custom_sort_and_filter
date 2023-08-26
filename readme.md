# AO3Scraper

Based off of [AO3Scraper](https://github.com/radiolarian/AO3Scraper)

Features:

-   Given a fandom, collection, or bookmarks URL, returns a list of the fic IDs and its html component
-   Sorts list of works by whatever, optionally filter out works in another list (say your bookmarked works)
-   Display sorted and filtered works in the same format as found on the AO3 site
    -   Done by exporting works to html files

## Dependencies

-   pip install bs4
-   pip install requests
-   pip install lxml

## Example Usage

Say you wanted first 100 English completed fics, ordered by kudos, in the Sherlock (TV) fandom.

### Steps:

1. Use AO3's filter feature on their website to get appropriate URL: http://archiveofourown.org/works?utf8=%E2%9C%93&work_search%5Bsort_column%5D=kudos_count&work_search%5Bother_tag_names%5D=&work_search%5Bquery%5D=&work_search%5Blanguage_id%5D=1&work_search%5Bcomplete%5D=0&work_search%5Bcomplete%5D=1&commit=Sort+and+Filter&tag_id=Sherlock+%28TV%29
2. Run `get_works.py`, enter args when prompted, leave blank to default to defaults, only URL and file_out are required
3. Run `process_works`, enter args when prompted, leave blank to default to defaults, only in_file is required
4. Open `[out].html` in browser

## License

just don't copy and stuff
