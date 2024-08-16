import requests
from bs4 import BeautifulSoup
import re
import dotenv
import os

dotenv.load_dotenv()

# Define DEF headers
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/'
}

# Define DEF proxies
proxies = {
    'http': os.getenv('VPN_PROXY'),
    'https': os.getenv('VPN_PROXY'),
}

# Define default host
host = 'https://1337x.to'


class Torrent:
    def __init__(self, title, seeds, leechers, link, size):
        self.title = title
        self.seeds = seeds
        self.leechers = leechers
        self.link = link
        self.size = size

    def __str__(self):
        return (f"Title: {self.title}, Seeds: {self.seeds}, Leechers: {self.leechers}, "
                f"Link: {self.link}, Size: {self.size}")


def search(query):
    url = f'{host}/search/{query}/1/'
    response = requests.get(url, headers=headers, proxies=proxies)

    soup = BeautifulSoup(response.content, 'html.parser')

    torrents = []
    rows = soup.find_all('tr')

    try:
        for row in rows:
            title_cell = row.find('td', class_='coll-1 name')
            seeds_cell = row.find('td', class_='coll-2 seeds')
            leechers_cell = row.find('td', class_='coll-3 leeches')
            size_cell = row.find('td', class_=lambda class_name: class_name and 'coll-4 size' in class_name)

            if title_cell and seeds_cell and leechers_cell:
                title = title_cell.find_all('a')[1].text.strip()
                seeds = seeds_cell.text.strip()
                leechers = leechers_cell.text.strip()
                link = 'https://1337x.to' + title_cell.find_all('a')[1]['href']

                size_text = size_cell.get_text(separator=' ').strip()
                size_match = re.match(r'([\d.]+\s[GMK]B)', size_text)
                size = size_match.group(1) if size_match else 'Unknown'
                # Create a Torrent object
                torrent = Torrent(title, seeds, leechers, link, size)
                # Fetch magnet link and update the Torrent object
            
                # Add the Torrent object to the list
                torrents.append(torrent)
    except Exception as e:
        print("Failed to parse the search results", e)

    return torrents



def get_magnet_link(link: str):
    # Make a request to the torrent detail page
    detail_response = requests.get(link, headers=headers, proxies=proxies)
    detail_soup = BeautifulSoup(detail_response.content, 'html.parser')
    
    # Find the magnet link in the torrent detail page
    magnet_tag = detail_soup.find('a', href=lambda href: href and href.startswith('magnet:'))
    return magnet_tag['href'] if magnet_tag else 'No magnet link found'
