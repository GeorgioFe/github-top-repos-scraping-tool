import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

base_url = 'https://github.com'


def get_topic_page(topic_url):
    response = requests.get(topic_url)
    if response.status_code != 200:
        raise Exception('Failed to load page {}'.format(topic_url))
    topic_parsed = BeautifulSoup(response.text, 'html.parser')
    return topic_parsed


def parse_star_count(stars_str):
    stars_str = stars_str.strip()
    if stars_str[-1] == 'k':
        return int(float(stars_str[:-1]) * 1000)
    return int(stars_str)


def get_repo_info(h3_tag, star_tag):
    """ Return all the required info about a repository. """
    a_tags = h3_tag.find_all('a')
    username = a_tags[0].text.strip()
    repo_name = a_tags[1].text.strip()
    repo_url = base_url + a_tags[1]['href']
    stars = parse_star_count(star_tag.text.strip())
    return username, repo_name, stars, repo_url


def get_topic_repos(parsed_doc):
    repo_tags = parsed_doc.find_all('h3', {
        'class': "f3 color-fg-muted text-normal lh-condensed"})
    star_tags = parsed_doc.find_all('span',
                                    {'class': "Counter js-social-count"})

    topic_repos_dict = {
        'username': [],
        'repo name': [],
        'stars': [],
        'repo URL': []
    }

    for i in range(len(repo_tags)):
        repo_info = get_repo_info(repo_tags[i], star_tags[i])
        topic_repos_dict['username'].append(repo_info[0])
        topic_repos_dict['repo name'].append(repo_info[1])
        topic_repos_dict['stars'].append(repo_info[2])
        topic_repos_dict['repo URL'].append(repo_info[3])

    return pd.DataFrame(topic_repos_dict)


def scrape_topic(topic_url, path):
    if os.path.exists(path):
        print("The file {} already exists. Skipping...".format(path))
        return
    topic_df = get_topic_repos(get_topic_page(topic_url))
    topic_df.to_csv(path, index=False)


def scrape_topics():
    topics_url = 'https://github.com/topics'
    response = requests.get(topics_url)
    if response.status_code != 200:
        raise Exception('Failed to load page {}'.format(topics_url))
    parsed_doc = BeautifulSoup(response.text, 'html.parser')

    topic_title_tags = parsed_doc.find_all('p', {
        'class': "f3 lh-condensed mb-0 mt-1 Link--primary"})
    topic_desc_tags = parsed_doc.find_all('p', {
        'class': "f5 color-fg-muted mb-0 mt-1"})
    topic_link_tags = parsed_doc.find_all('a', {
        'class': "no-underline flex-1 d-flex flex-column"})

    topic_titles = [topic.text for topic in topic_title_tags]
    topic_descs = [topic.text.strip() for topic in topic_desc_tags]
    topic_urls = [base_url + topic['href'] for topic in topic_link_tags]

    topics_dict = {
        'Title': topic_titles,
        'Description': topic_descs,
        'URL': topic_urls
    }

    return pd.DataFrame(topics_dict)


def scrape_topics_repos():
    print('Scraping list of topics')
    topics_df = scrape_topics()

    os.makedirs('Topics Data', exist_ok=True)
    for index, row in topics_df.iterrows():
        print('Scraping top repositories for "{}"'.format(row['Title']))
        scrape_topic(row['URL'], 'Topics Data/{}.csv'.format(row['Title']))


scrape_topics_repos()
