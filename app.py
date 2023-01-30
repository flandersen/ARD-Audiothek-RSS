import html
import json
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


if __name__ == '__main__':

    show_id = "10777871" # Kalk & Welk
    latest = "10"

    query = QUERY_TEMPLATE.replace('{SHOW_ID}', show_id)
    query = query.replace('{LATEST}', latest)
    json_data = {"query": query}

    with requests.post(URL, json=json_data) as response:
        if response.status_code == STATUS_CODE_GOOD:
            json_obj = json.loads(response.text)
            show = json_obj['data']["programSet"]
            image_url = escape_string(show["image"]["url1X1"])
            image_url = image_url.replace("{width}", "448")
            show_synopsis = escape_string(show["synopsis"])
            show_titel = escape_string(show["title"])
            
            with open("D:\\Projects\\ard-audiothek\\rssfeed.xml", "w", encoding='utf8') as w:
                w.write('<rss xmlns:atom="http://www.w3.org/2005/Atom" xmlns:media="http://search.yahoo.com/mrss/" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" version="2.0">')
                w.write('<channel>')
                w.write('<title>{}</title>'.format(show_titel))
                w.write('<link>{}</link>'.format(show['sharingUrl']))
                w.write('<image>')
                w.write('<url>{}</url>'.format(image_url))
                w.write('<title>{}</title>'.format(show_titel))
                w.write('<link>https://www.ardaudiothek.de{}</link>'.format(show["path"]))
                w.write('</image>')
                w.write('<description>{}</description>'.format(show_synopsis))

                for item in show["items"]["nodes"]:
                    audio = item['audios'][0]
                    audio_url = escape_string(audio['url'])
                    download_url = escape_string(audio['downloadUrl'])
                    duration = item['duration']
                    length = get_file_length(audio['url'])
                    publication_date = item['publicationStartDateAndTime']
                    sharing_url = escape_string(item['sharingUrl'])
                    synopsis = escape_string(item['synopsis'])
                    titel = escape_string(item['title'])
                   
                    w.write('<item>')
                    w.write('<title>{}</title>'.format(titel))
                    w.write('<description>{}</description>'.format(synopsis))
                    w.write('<guid>{}</guid>'.format(sharing_url))
                    w.write('<link>{}</link>'.format(download_url))
                    w.write('<enclosure url="{}" length="{}" type="audio/mpeg"/>'.format(audio_url, length))
                    w.write('<media:content url="{}" medium="audio" duration="{}" type="audio/mpeg"/>'.format(download_url, duration))
                    w.write('<pubDate>{}</pubDate>'.format(publication_date))
                    w.write('<itunes:duration>{}</itunes:duration>'.format(duration))
                    w.write('</item>')

                w.write('</channel>')
                w.write('</rss>')
