import html
import json
from io import TextIOWrapper

import requests

URL = 'https://api.ardaudiothek.de/graphql'
QUERY_TEMPLATE ="""
{
    programSet(id:{SHOW_ID})
    {
        title
        ,path
        ,synopsis
        ,sharingUrl
        ,image
        {
            url
            ,url1X1
        }
        ,items(
            orderBy:PUBLISH_DATE_DESC
            ,filter:
            {
                isPublished:
                {
                    equalTo:true
                }
            }
            first:{LATEST}
        )
        {
            nodes
            {
                title
                ,summary
                ,synopsis
                ,sharingUrl
                ,publicationStartDateAndTime: publishDate
                ,url
                ,episodeNumber
                ,duration
                ,isPublished
                ,audios
                {
                    url
                    ,downloadUrl
                    ,size
                    ,mimeType
                }
            }
        }
    }
}
"""

STATUS_CODE_GOOD = 200

def escape_string(str:str)->str:
    return html.escape(str)

def get_header(url:str):
    with requests.get(url) as response:
        return response.headers

def get_file_length(url):
    header = get_header(url)
    return header['content-length']

def process_response_text(text:str):
    json_obj = json.loads(text)
    show = json_obj['data']["programSet"]
    process_show(show)

def process_show(show:dict):
    image_url = escape_string(show["image"]["url1X1"])
    image_url = image_url.replace("{width}", "448")
    show_synopsis = escape_string(show["synopsis"])
    show_titel = escape_string(show["title"])
    
    with open("rssfeed.xml", "w", encoding='utf8') as writer:
        writer.write('<rss xmlns:atom="http://www.w3.org/2005/Atom" xmlns:media="http://search.yahoo.com/mrss/" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" version="2.0">\n')
        writer.write('    <channel>\n')
        writer.write('        <title>{}</title>\n'.format(show_titel))
        writer.write('        <link>{}</link>\n'.format(show['sharingUrl']))
        writer.write('        <image>\n')
        writer.write('            <url>{}</url>\n'.format(image_url))
        writer.write('            <title>{}</title>\n'.format(show_titel))
        writer.write('            <link>https://www.ardaudiothek.de{}</link>\n'.format(show["path"]))
        writer.write('        </image>\n')
        writer.write('        <description>{}</description>\n'.format(show_synopsis))

        process_episodes(show, writer)

        writer.write('    </channel>\n')
        writer.write('</rss>\n')

def process_episodes(show:dict, writer:TextIOWrapper):
    for item in show["items"]["nodes"]:
        process_episode(item, writer)

def process_episode(item:dict, writer:TextIOWrapper):
    if len(item['audios']) > 0:
        audio = item['audios'][0]
        audio_url = escape_string(audio['url'])
        download_url = escape_string(audio['downloadUrl'])
        duration = item['duration']
        length = get_file_length(audio['url'])
        publication_date = item['publicationStartDateAndTime']
        sharing_url = escape_string(item['sharingUrl'])
        synopsis = escape_string(item['synopsis'])
        titel = escape_string(item['title'])
        indent = '        '
        writer.write('{}<item>\n'.format(indent))
        writer.write('{}    <title>{}</title>\n'.format(indent, titel))
        writer.write('{}    <description>{}</description>\n'.format(indent, synopsis))
        writer.write('{}    <guid>{}</guid>\n'.format(indent, sharing_url))
        writer.write('{}    <link>{}</link>\n'.format(indent, download_url))
        writer.write('{}    <enclosure url="{}" length="{}" type="audio/mpeg"/>\n'.format(indent, audio_url, length))
        writer.write('{}    <media:content url="{}" medium="audio" duration="{}" type="audio/mpeg"/>\n'.format(indent, download_url, duration))
        writer.write('{}    <pubDate>{}</pubDate>\n'.format(indent, publication_date))
        writer.write('{}    <itunes:duration>{}</itunes:duration>\n'.format(indent, duration))
        writer.write('{}</item>\n'.format(indent))    


if __name__ == '__main__':

    show_id = "10777871" # Kalk & Welk
    latest = "10"

    query = QUERY_TEMPLATE.replace('{SHOW_ID}', show_id)
    query = query.replace('{LATEST}', latest)
    json_data = {"query": query}

    with requests.post(URL, json=json_data) as response:
        if response.status_code == STATUS_CODE_GOOD:
            process_response_text(response.text)