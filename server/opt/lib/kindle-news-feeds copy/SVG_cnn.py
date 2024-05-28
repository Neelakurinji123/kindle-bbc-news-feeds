#!/usr/bin/env python3
# encoding=utf-8
# -*- coding: utf-8 -*-

# Written by : krishna@hottunalabs.net
# Update     : 26 May 2024 

import json, os, sys, re, io
#import time as t
from datetime import datetime, timedelta, date
from pytz import timezone
import requests
from urllib.request import urlopen
import feedparser
import xml.etree.ElementTree as ET
from subprocess import Popen
from lxml import html
from html.parser import HTMLParser
from xml.dom import minidom
from PIL import ImageFont
from wand.image import Image
from wand.display import display
from cairosvg import svg2png
#import astral
from astral import LocationInfo
from astral.sun import sun
import qrcode
import qrcode.image.svg
from qrcode.image.pure import PyPNGImage
import SVGtools

user_setting = 'config/user.xml'

def daytime(config):
    # dark mode
    #tree = ET.parse('display.xml')
    #root = tree.getroot()
    lat = config['lat'] if 'lat' in config else None
    lon = config['lon'] if 'lon' in config else None
    zone = config['timezone']
    tz = timezone(zone)
    offset = datetime.now(tz).utcoffset().seconds
    now = config['now']
    try:
        city, region = zone.split('/')
    except:
        city = zone
        region = str()
    location = LocationInfo(city, region, zone, lat, lon)
    s = sun(location.observer, date=date.today(), tzinfo=tz)
    _sunrise, _sunset = s['sunrise'], s['sunset']
    sunrise, sunset = int(_sunrise.timestamp()), int(_sunset.timestamp())
    if sunrise >= now or sunset <= now:
        state = 'night'
    else:
        state = 'day'
    return state    

def read_config(setting, user=None):
    config = dict()
    tree = ET.parse(setting)
    root = tree.getroot()
    for service in root.findall('service'):
        if service.get('name') == 'station':
            config['template'] = service.find('template').text
            config['category'] = service.find('category').text
            config['breaking_news'] = bool(eval(service.find('breaking_news_only').text))
            config['entries'] = 1 if config['breaking_news'] == True else int(service.find('entries').text)
            config['logo'] = service.find('logo').text
            config['logo_image'] = service.find('logo_image').text
            config['layout'] = service.find('layout').text
        elif service.get('name') == 'env':
            config['kindle'] = dict()
            config['kindle']['duration'] = int(service.find('duration').text)
            config['kindle']['repeat'] = int(service.find('repeat').text)
            config['kindle']['display_reset'] = bool(eval(service.find('display_reset').text))
            config['kindle']['post_run'] = service.find('post_run').text

    template_file='template/' + config['template'] + '.xml'
    tree = ET.parse(template_file)
    root = tree.getroot()

    for station in root.findall('station'):
        if station.get('name') == config['category']:
            config['url'] = station.find('url').text
            config['image_path'] = station.find('img_path').text
    # sheet config
    tree = ET.parse(config['layout'])
    root = tree.getroot()
    config['layout'] = dict()
    for service in root.findall('service'):
        if service.get('name') == 'paper':
            config['layout']['paper_layout'] = service.find('paper_layout').text
            config['layout']['encoding'] = service.find('encoding').text
            config['layout']['font'] = service.find('font').text
            #config['layout']['italic_font'] = service.find('italic_font').text
            #config['layout']['bold_font'] = service.find('bold_font').text
            config['layout']['title_font_size'] = int(service.find('title_font_size').text)
            config['layout']['title_font_space'] = int(service.find('title_font_space').text)
            config['layout']['title_row_length'] = int(service.find('title_row_length').text)
            config['layout']['title_rows'] = int(service.find('title_rows').text)
            config['layout']['title_y_padding'] = int(service.find('title_y_padding').text)
            config['layout']['summary_font_size'] = int(service.find('summary_font_size').text)
            config['layout']['summary_font_space'] = int(service.find('summary_font_space').text)
            config['layout']['summary_row_length'] = int(service.find('summary_row_length').text)
            config['layout']['summary_rows'] = int(service.find('summary_rows').text)
            config['layout']['summary_y_padding'] = int(service.find('summary_y_padding').text)
            config['layout']['img_effect'] = int(service.find('img_effect').text)
    # user config
    if not user == None:
        tree = ET.parse(user)
        root = tree.getroot()
        for service in root.findall('service'):
            if service.get('name') == 'user':
                config['timezone'] = service.find('timezone').text
                #config['dark_mode'] = service.find('dark_mode').text
                config['lat'] = float(service.find('lat').text) if not service.find('lat').text == None else 0
                config['lon'] = float(service.find('lon').text) if not service.find('lon').text == None else 0
    else:
        config['timezone'] = 'GMT'
        #config['dark_mode'] = 'False'
        config['lat'] = '0'
        config['lon'] = '0'
    tz = timezone(config['timezone'])
    config['now'] = int(datetime.now(tz).timestamp())
    return config

def get_source(url, entries=1):
    source = feedparser.parse(url)
    ent = list()
    for n in range(0, entries):
        d = dict()
        d['link'] = source['entries'][n]['link']
        d['media_thumbnail'] = source['entries'][n]['media_thumbnail'][0]['url']
        a = source['entries'][n]['published_parsed']
        d['published'] = [a[0], a[1], a[2], a[3], a[4], a[5], 0]
        d['summary'] = source['entries'][n]['summary']
        d['title'] = source['entries'][n]['title']
        ent.append(d)
    return ent

class WordProccessing:
    def __init__(self, config, entry):
        self.config = config
        self.link = entry['link']
        self.media_thumbnail = entry['media_thumbnail']
        self.published = entry['published']
        self.summary = entry['summary']
        self.title = entry['title']
        
    def png(self, svg=None):
        config = self.config
        layout = config['layout']
        link = self.link
        media_thumbnail = self.media_thumbnail
        published = self.published
        _summary = self.summary
        _title = self.title
        zone = config['timezone']
        now = config['now']
        tz = timezone(zone)
        # News clip
        png_clip = self.img_clip()
        # Logo png
        png_logo = self.img_logo()
        # QR code
        img = qrcode.make(link)
        png_qr = io.BytesIO()
        img.save(png_qr)
        png_qr_val = png_qr.getvalue()
        # SVG body
        png_body = io.BytesIO()
        svg2png(bytestring=svg, write_to=png_body, background_color="white", parent_width=800, parent_height=600)
        png_body_val = png_body.getvalue() 
            
        with Image(blob=png_body_val) as bg_img:
            # QR image
            with Image(blob=png_qr_val) as fg_img:
                fg_img.resize(200, 200)
                #bg_img.composite(fg_img, left=20, top=385)
                bg_img.composite(fg_img, left=20, top=265)
                bg_img.format = 'png'
                bg_img.save(filename='test_conposite1.png')
            fg_img.close()
            # Logo image
            with Image(blob=png_logo) as fg_img:
                #bg_img.composite(fg_img, left=40, top=290)
                bg_img.composite(fg_img, left=40, top=485)
                bg_img.format = 'png'
                bg_img.save(filename='test_conposite2.png')
            fg_img.close()
            # Image clip
            with Image(blob=png_clip) as fg_img:
                # image ratio: (16:9)
                bg_img.composite(fg_img, left=(800 - 560), top=(600 - 315))
                bg_img.format = 'png'
                bg_img.save(filename='test_conposite2.png')
            fg_img.close()
            
            display(bg_img)
        bg_img.close()

        return png_qr
        
    def img_clip(self):
        config = self.config
        layout = config['layout']
        media_thumbnail = self.media_thumbnail
        clip = urlopen(media_thumbnail)
        try:
            with Image(file=clip) as img:
                with img.clone() as i:
                    i.resize(560, 315) # 16:9
                    if layout['img_effect'] == 1:
                        i.transform_colorspace('gray')
                        #i.ordered_dither('h6x6a')
                        i.color_threshold(start='#333', stop='#cdc')
                        png_blob = i.make_blob('png')
        finally:
            clip.close()
        return png_blob

    def img_logo(self):
        config = self.config
        logo_image = config['logo_image']
        with Image(filename=logo_image) as img:
            with img.clone() as i:
                    i.transform(resize='160x80>')
                    #i.transform_colorspace('gray')
                    png_blob = i.make_blob('png')
        return png_blob        
        
    def svg(self):
        config = self.config
        layout = config['layout']
        link = self.link
        media_thumbnail = self.media_thumbnail
        published = self.published
        _summary = self.summary
        _title = self.title
        zone = config['timezone']
        now = config['now']
        tz = timezone(zone)
        body = str()
        if layout['paper_layout'] == 'landscape':
            width, height = 800, 600
        else:
            width, height = 600, 800
        header = '<?xml version="1.0" encoding="' + layout['encoding'] + '"?>\n'
        header += '<svg xmlns="http://www.w3.org/2000/svg" height="{}" width="{}" version="1.1" xmlns:xlink="http://www.w3.org/1999/xlink">\n'.format(height, width)
        header += '<g font-family="' + layout['font'] + '">\n'
    
        # maintenant
        maintenant = (str.lower(datetime.fromtimestamp(now, tz).strftime('%a, %d %b %H:%M')))
        # published
        utc = timezone('UTC')
        published.append(utc)
        d = datetime(*published)
        time = d.timestamp()
        hr = int((now - time) / 3600)
        mi = int((now - time) % 60)
        ago = str(mi) + ' mins ago' if hr == 0 else str(hr) + ' hrs ago'           
        body += SVGtools.text('start', '30px', 20, 40, maintenant).svg()
        #site = config['logo'] + ' ' + config['category']
        #body += SVGtools.text('end', '30px', 780, 40, site).svg()
        body += SVGtools.text('end', '30px', 780, 40, ago).svg()
        body += '</g>\n'
        kwargs1 = {'rows': layout['title_rows'], 'row_length': layout['title_row_length'], 'font': layout['font'], 
                    'font_size': layout['title_font_size'], 'min_sp': layout['title_font_space'], 'y_padding': layout['title_y_padding']}
        title = self.wordwrap(paragraph=_title, **kwargs1)
        kwargs2 = {'rows': layout['summary_rows'], 'row_length': layout['summary_row_length'], 'font': layout['font'],
                    'font_size': layout['summary_font_size'], 'min_sp': layout['summary_font_space'], 'y_padding': layout['summary_y_padding']}
        summary = self.wordwrap(paragraph=_summary, **kwargs2)
        # svg text
        x, y = 50, 120
        a, y = self.text_proccessing(x=x, y=y, paragraph=title, **kwargs1)
        body += a
        x, y = 60, y + 10
        a, y = self.text_proccessing(x=x, y=y, paragraph=summary, **kwargs2)
        body += a
        footer = '</svg>\n'
        return header + body + footer

    def text_proccessing(self, x, y, rows, row_length, font, font_size, min_sp, paragraph, y_padding):
        f = ImageFont.truetype(font, font_size)
        row = 1
        _x = x
        a = '<g font-family="{}">\n'.format(font)
        for t in paragraph:
            if len(t) > 2 and not len(paragraph) == row:
                _sp = int((row_length - f.getlength(''.join(t))) / (len(t) - 1))
                for s in t:
                    a += SVGtools.text(anchor='start', fontsize=str(font_size) + 'px', x=_x, y=y, v=s).svg()
                    _x += int(f.getlength(s)) + _sp
            else:
                for s in t:
                    a += SVGtools.text(anchor='start', fontsize=str(font_size) + 'px', x=_x, y=y, v=s).svg()
                    _x += int(f.getlength(s)) + min_sp
            _x = x
            y += y_padding
            row += 1                      
        return a + '</g>\n', y
        
    def wordwrap(self, rows, row_length, font, font_size, min_sp, paragraph, y_padding):
        f = ImageFont.truetype(font, font_size)
        s = list()
        d = dict()
        rows -= 1
        row = 0
        for w in paragraph.split():
            if f.getlength(''.join(s)) + f.getlength(w)  + (min_sp * len(s)) > row_length and row < rows:
                d[row] = s
                row += 1
                s = [w]
                d[row] = s
            elif f.getlength(''.join(s)) + f.getlength(w)  + (min_sp * len(s)) + f.getlength('...') > row_length and row == rows:
                s.append('...')
                d[row] = s
                break
            else:
                s.append(w)
                d[row] = s
        return [ x[1] for x in sorted(d.items())] 


def build_source(NewsFeeds, title, summary, entries):
    data = list()
    news = dict()
    for i in range(0, entries_number):
        news['head'] = NewsFeeds.feed['title']
        news['logo'] = logo
        entries = NewsFeeds.entries[i]
        for k, v in entries.items():
            if k == 'summary':

                # hmm, tricky problem...
                entries[k] = entries[k].replace("\"", "\'\'")       # Double Quotation Mark
                entries[k] = entries[k].replace(u"\u2018", "\'")    # Left Single Quotation Mark
                entries[k] = entries[k].replace(u"\u2019", "\'")    # Right Single Quotation Mark
                entries[k] = entries[k].replace(u"\u2013", "-")     # En Dash
                entries[k] = entries[k].replace(u"\u2014", "--")    # Em Dash
                news['summary'] = summary.proccessing(entries[k])
            elif k == 'title':
                entries[k] = entries[k].replace("\"", "\'\'")
                entries[k] = entries[k].replace(u"\u2018", "\'")
                entries[k] = entries[k].replace(u"\u2019", "\'")
                entries[k] = entries[k].replace(u"\u2013", "-")
                entries[k] = entries[k].replace(u"\u2014", "--")
                news['title'] = title.proccessing(entries[k])
            elif k == 'published':
                news['published'] = entries[k]
            elif k == 'link':
                page = requests.get(entries[k])
                tree = html.fromstring(page.content)

                for m in tree.xpath(img_path):
                    img_url = m.get("content")
                    file1 = working_dir + 'image' + str(i)
                    file2 = working_dir + 'image' + str(i) + '.bmp'
                    file3 = working_dir + 'image' + str(i) + '.svg'
                    file4 = working_dir + 'image' + str(i) + '.png'
                    args1 = ['wget', '-q', img_url, '-O', file1]
                    args2 = ['convert', '-enhance', '-equalize', '-contrast', '-resize', '600x338!', file1, file2]

                    if dark_mode == 'True':
                        args3 = ['potrace', '-i', '--svg', file2, '-o', file3]
                    else:
                        args3 = ['potrace', '--svg', file2, '-o', file3]

                    args4 = ['gm', 'convert',  '-size', '600x!', '-background', 'white', '-depth', '8' ,file3, file4]

                    output = Popen(args1)
                    t.sleep(5)
                    output = Popen(args2)
                    t.sleep(5)
                    output = Popen(args3)
                    t.sleep(5)
                    output = Popen(args4)

                    doc = minidom.parse(file3)
                    svg_path = [path.getAttribute('d') for path
                                in doc.getElementsByTagName('path')]
                    doc.unlink()
                    news['img'] = svg_path

        data += [news]
        news = dict()

    return data



#    n = 0
#    for news in news_data:
#        filename = working_dir + 'entries' + str(n) + '.svg'
#        output_file = working_dir2 + 'entries' + str(n) + '.png'
#        create_svg(news, filename)

#        if dark_mode == 'True':
#            #args = ['convert', '-size', '600x800',  '-background', 'white', '-depth', '8', '-negate', filename, output_file]
#            args = ['gm', 'convert', '-size', '600x800', '-background', 'white', '-depth', '8', '-resize', '600x800', '-colorspace', 'gray', '-type', 'palette', '-geometry', '600x800', '-negate', filename, output_file]
 #           output = Popen(args)
 #       else:
 #           #args = ['convert', '-size', '600x800',  '-background', 'white', '-depth', '8', filename, output_file]
 #           args = ['gm', 'convert', '-size', '600x800', '-background', 'white', '-depth', '8', '-resize', '600x800', '-colorspace', 'gray', '-type', 'palette', '-geometry', '600x800', filename, output_file]
 #           output = Popen(args)

 #       n += 1


    # create control file
    control_file = working_dir2 + 'control.env'

    svg_file = open(control_file, "w")

    svg_file.write('duration_time=' + duration_time + '\n')
    svg_file.write('repeat=' + repeat + '\n')
    svg_file.write('display_reset="' + display_reset + '"\n')
    svg_file.close()

if __name__ == "__main__":
    flag_dump, flag_config = False, False
    if 'dump' in sys.argv:
        flag_dump = True
        sys.argv.remove('dump')
    elif 'config' in sys.argv:
        flag_config = True
        sys.argv.remove('config')
        
    # Use custom settings    
    if len(sys.argv) > 1:
        a = sys.argv[1]
    else:
        a = "settings.xml"

    config = read_config(setting=a, user=user_setting)
    entries = get_source(config['url'], entries=2)
    #entries = get_source(config['url'], entries=2)
    state = daytime(config=config)
    if  flag_dump == True:
        #import pprint
        print(json.dumps(config, indent=4, ensure_ascii=False))
        for entry in entries:
            print(json.dumps(entry, indent=4, ensure_ascii=False))
        exit(0)
    elif flag_config == True:
        print(json.dumps(config, indent=4, ensure_ascii=False))
        exit(0)
    n = 1    
    for entry in entries:
        p = WordProccessing(config=config, entry=entry)
        svg = p.svg()
        p.png(svg=svg)
        
        #print('test234', svg)
        with open( str(n)+'test.svg', 'w') as f:
            f.write(svg)

        #p.png()
        #png_qr = p.png()
        #png_qr = p.png(svg=svg)
        ##with open(str(n)+'qr_test.png', 'wb') as f:
        ##    f.write(png_qr.getvalue())
        #png_qr_val = png_qr.getvalue()
        #with Image(blob=png_qr_val) as img:
        #    print('width =', img.width)
        #    print('height =', img.height)
        #    img.format = 'png'
        #    img.save(filename=str(n)+'qr_test.png')
        #    n += 1

 #stream = io.BytesIO(clip.raw)

 #with Image(filename=stream) as img:
 #    with img.clone() as i:
 #        i.rotate(90)
 #        i.alpha_channel_types = 'flatten'
 #        i.negate(True,"all_channels")
 #        i.save(filename='testnew.png')
         
 #i = clip.getvalue().decode()
 
 #with open("testnew.png","wb") as f:
 #    f.write(stream.getvalue())
 #print(clip.status_code)           
        

#    for n in range(0,len(entries)):
#        print( entries[n])
    #data = build_source(config=config, entries=entries)
    #svg = create_svg(config=config, entries=entries)
        
        #with Image(blob=png_qr_val) as img:
        #    print('width =', img.width)
        #    print('height =', img.height)
        #    img.format = 'png'
        #    img.save(filename=str(n)+'qr_test.png'
        
            
        #return png_qr    
    
#from urllib.request import urlopen
#with urlopen('https://pypi.org/pypi/sampleproject/json') as resp:


