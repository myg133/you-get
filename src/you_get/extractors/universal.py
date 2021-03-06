#!/usr/bin/env python

__all__ = ['universal_download']

from ..common import *
from .embed import *

def get_m3u8_files(url):
    urls = general_m3u8_extractor(url)
    if len(urls)==1:
        urls = get_m3u8_files(urls[0])
    return urls

def universal_download(origin_url, output_dir='.', merge=True, info_only=False, **kwargs):
    url = origin_url
    if r1(r'.*(\.m3u8).*',origin_url): #m3u8 Url
        global output_filename
        title = output_filename
        propties = origin_url.split("!!")
        url = propties[0]
        if len(propties)>0:
            title = propties[-1]
        if not title:
            raise ("output-filename is required when download m3u8\n"
            " or add filename to the head of url,\n"
            " and name can not be chinese, like:\n"
            " http://xxxx.m3u8!!aa")
        if os.path.exists(os.path.join(output_dir, title+".mkv")):
            return 
        urls = get_m3u8_files(url)
        try:
            download_urls(urls, title, 'ts', 0, output_dir, merge=True)
        except Exception as identifier:
            pass
        
        return

    try:
        content_type = get_head(url, headers=fake_headers)['Content-Type']
    except:
        content_type = get_head(url, headers=fake_headers, get_method='GET')['Content-Type']
    if content_type.startswith('text/html'):
        try:
            embed_download(url, output_dir=output_dir, merge=merge, info_only=info_only, **kwargs)
        except Exception:
            pass
        else:
            return

    domains = url.split('/')[2].split('.')
    if len(domains) > 2: domains = domains[1:]
    site_info = '.'.join(domains)

    if content_type.startswith('text/html'):
        # extract an HTML page
        response = get_response(url, faker=True)
        page = str(response.data)

        page_title = r1(r'<title>([^<]*)', page)
        if page_title:
            page_title = unescape_html(page_title)

        meta_videos = re.findall(r'<meta property="og:video:url" content="([^"]*)"', page)
        if meta_videos:
            try:
                for meta_video in meta_videos:
                    meta_video_url = unescape_html(meta_video)
                    type_, ext, size = url_info(meta_video_url)
                    print_info(site_info, page_title, type_, size)
                    if not info_only:
                        download_urls([meta_video_url], page_title,
                                      ext, size,
                                      output_dir=output_dir, merge=merge,
                                      faker=True)
            except:
                pass
            else:
                return

        hls_urls = re.findall(r'(https?://[^;"\'\\]+' + '\.m3u8?' +
                              r'[^;"\'\\]*)', page)
        if hls_urls:
            try:
                for hls_url in hls_urls:
                    type_, ext, size = url_info(hls_url)
                    print_info(site_info, page_title, type_, size)
                    if not info_only:
                        download_url_ffmpeg(url=hls_url, title=page_title,
                                            ext='mp4', output_dir=output_dir)
            except:
                pass
            else:
                return

        # most common media file extensions on the Internet
        media_exts = ['\.flv', '\.mp3', '\.mp4', '\.webm',
                      '[-_]1\d\d\d\.jpe?g', '[-_][6-9]\d\d\.jpe?g', # tumblr
                      '[-_]1\d\d\dx[6-9]\d\d\.jpe?g',
                      '[-_][6-9]\d\dx1\d\d\d\.jpe?g',
                      '[-_][6-9]\d\dx[6-9]\d\d\.jpe?g',
                      's1600/[\w%]+\.jpe?g', # blogger
                      'img[6-9]\d\d/[\w%]+\.jpe?g' # oricon?
        ]

        urls = []
        for i in media_exts:
            urls += re.findall(r'(https?://[^ ;&"\'\\<>]+' + i + r'[^ ;&"\'\\<>]*)', page)

            p_urls = re.findall(r'(https?%3A%2F%2F[^;&"]+' + i + r'[^;&"]*)', page)
            urls += [parse.unquote(url) for url in p_urls]

            q_urls = re.findall(r'(https?:\\\\/\\\\/[^ ;"\'<>]+' + i + r'[^ ;"\'<>]*)', page)
            urls += [url.replace('\\\\/', '/') for url in q_urls]

        # a link href to an image is often an interesting one
        urls += re.findall(r'href="(https?://[^"]+\.jpe?g)"', page, re.I)
        urls += re.findall(r'href="(https?://[^"]+\.png)"', page, re.I)
        urls += re.findall(r'href="(https?://[^"]+\.gif)"', page, re.I)

        # <img> with high widths
        urls += re.findall(r'<img src="([^"]*)"[^>]*width="\d\d\d+"', page, re.I)

        # relative path
        rel_urls = []
        rel_urls += re.findall(r'href="(\.[^"]+\.jpe?g)"', page, re.I)
        rel_urls += re.findall(r'href="(\.[^"]+\.png)"', page, re.I)
        rel_urls += re.findall(r'href="(\.[^"]+\.gif)"', page, re.I)
        for rel_url in rel_urls:
            urls += [ r1(r'(.*/)', url) + rel_url ]

        # MPEG-DASH MPD
        mpd_urls = re.findall(r'src="(https?://[^"]+\.mpd)"', page)
        for mpd_url in mpd_urls:
            cont = get_content(mpd_url)
            base_url = r1(r'<BaseURL>(.*)</BaseURL>', cont)
            urls += [ r1(r'(.*/)[^/]*', mpd_url) + base_url ]

        # have some candy!
        candies = []
        i = 1
        for url in set(urls):
            filename = parse.unquote(url.split('/')[-1])
            if 5 <= len(filename) <= 80:
                title = '.'.join(filename.split('.')[:-1]) or filename
            else:
                title = '%s' % i
                i += 1

            if r1(r'(https://pinterest.com/pin/)', url):
                continue

            candies.append({'url': url,
                            'title': title})

        for candy in candies:
            try:
                try:
                    mime, ext, size = url_info(candy['url'], faker=False)
                    assert size
                except:
                    mime, ext, size = url_info(candy['url'], faker=True)
                    if not size: size = float('Inf')
            except:
                continue
            else:
                print_info(site_info, candy['title'], ext, size)
                if not info_only:
                    try:
                        download_urls([candy['url']], candy['title'], ext, size,
                                      output_dir=output_dir, merge=merge,
                                      faker=False)
                    except:
                        download_urls([candy['url']], candy['title'], ext, size,
                                      output_dir=output_dir, merge=merge,
                                      faker=True)
        return

    else:
        # direct download
        url_trunk = url.split('?')[0]  # strip query string
        filename = parse.unquote(url_trunk.split('/')[-1]) or parse.unquote(url_trunk.split('/')[-2])
        title = '.'.join(filename.split('.')[:-1]) or filename
        _, ext, size = url_info(url, faker=True)
        print_info(site_info, title, ext, size)
        if not info_only:
            download_urls([url], title, ext, size,
                          output_dir=output_dir, merge=merge,
                          faker=True)
        return

site_info = None
download = universal_download
download_playlist = playlist_not_supported('universal')
