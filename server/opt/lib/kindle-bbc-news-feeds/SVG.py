#!/usr/bin/env python3
# encoding=utf-8
# -*- coding: utf-8 -*-

# Written by : krishna@hottunalabs.net
# Update     : 26 May 2024 

import json, os, sys, re, io
import time as t
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

def read_config(setting, user=None):
    config = dict()
    tree = ET.parse(setting)
    root = tree.getroot()
    for service in root.findall('service'):
        if service.get('name') == 'station':
            config['template'] = service.find('template').text
            config['category'] = service.find('category').text
            config['breaking_news'] = bool(eval(service.find('breaking_news_only').text)) if service.find('breaking_news_only') is not None else None
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
                config['timezone'] = service.find('timezone').text if service.find('timezone').text is not None else 'UTC'
                #config['dark_mode'] = service.find('dark_mode').text
                config['lat'] = float(service.find('lat').text) if service.find('lat').text is not None else 0
                config['lon'] = float(service.find('lon').text) if service.find('lon').text is not None else 0
    else:
        config['timezone'] = 'UTC'
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
                bg_img.composite(fg_img, left=20, top=285)
                bg_img.format = 'png'
            fg_img.close()
            # Logo image
            with Image(blob=png_logo) as fg_img:
                #bg_img.composite(fg_img, left=40, top=290)
                bg_img.composite(fg_img, left=40, top=500)
                bg_img.format = 'png'
            fg_img.close()
            # Image clip
            with Image(blob=png_clip) as fg_img:
                # image ratio: (16:9)
                bg_img.composite(fg_img, left=(800 - 560), top=(600 - 315))
                bg_img.format = 'png'
            fg_img.close()
            img_blob = bg_img.make_blob('png')
            #display(bg_img)
        bg_img.close()
        return img_blob
        
    def img_clip(self):
        config = self.config
        layout = config['layout']
        media_thumbnail = self.media_thumbnail
        clip = urlopen(media_thumbnail)
        try:
            with Image(file=clip) as img:
                with img.clone() as i:
                    i.resize(560, 315) # 16:9
                    if layout['img_effect'] == 0:  # grey
                        i.transform_colorspace('gray')
                        png_blob = i.make_blob('png')
                    if layout['img_effect'] == 1:  # Color Threshold
                        i.color_threshold(start='#333', stop='#cdc')
                        png_blob = i.make_blob('png')
                    elif layout['img_effect'] == 2:  # Auto Threshold ('triangle'))
                        i.auto_threshold(method='triangle')
                        png_blob = i.make_blob('png')
                    elif layout['img_effect'] == 3: # Adaptive Threshold
                        i.transform_colorspace('gray')
                        i.adaptive_threshold(width=16, height=16,
                            offset=-0.08 * i.quantum_range)
                        png_blob = i.make_blob('png')
                    elif layout['img_effect'] == 4: # Ordered Dither (Circles 6x6)
                        i.transform_colorspace('gray')
                        i.ordered_dither('c6x6b')
                        png_blob = i.make_blob('png')
                    elif layout['img_effect'] == 5: # Random Threshold
                        i.transform_colorspace('gray')
                        i.random_threshold(low=0.3 * i.quantum_range,
                             high=0.6 * i.quantum_range)
                        png_blob = i.make_blob('png')
                    elif layout['img_effect'] == 6: # Range Threshold (soft)
                        i.transform_colorspace('gray')
                        white_point = 0.9 * i.quantum_range
                        black_point = 0.2 * i.quantum_range
                        delta = 0.05 * i.quantum_range
                        i.range_threshold(low_black=black_point - delta,
                            low_white=white_point - delta,
                            high_white=white_point + delta,
                            high_black=black_point + delta)
                        png_blob = i.make_blob('png')
        finally:
            clip.close()
        return png_blob

    def img_logo(self):
        config = self.config
        logo_image = config['logo_image']
        timezone = config['timezone']
        lat = config['lat']
        lon = config['lon']
        state = self.daytime() if not timezone == 'GMT' and not lat == 0 and not lon == 0 else 'night'
        with Image(filename=logo_image) as img:
            with img.clone() as i:
                    i.transform(resize='160x80>')
                    if state == 'day':
                        i.level(black=0.0, white=None, gamma=5.0)
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
        da = int((now - time) / 86400)
        hr = int((now - time) / 3600)
        mi = int((now - time) % 60)
        ago = str(mi) + ' mins ago' if hr == 0 else str(hr) + ' hrs ago'
        ago = str(da) + ' days ago' if not da == 0 else ago         
        body += SVGtools.text('start', '30px', 20, 40, ( 'created at ' + maintenant)).svg()
        #site = config['logo'] + ' ' + config['category']
        #body += SVGtools.text('end', '30px', 780, 40, site).svg()
        body += SVGtools.text('end', '30px', 780, 40, ago).svg()
        body += '</g>\n'
        style = 'stroke:rgb(128,128,128);stroke-width:1px;'
        body += SVGtools.line(x1=(0), x2=(800), y1=(50), y2=(50), style=style).svg()
        
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
        (x, y) = (60, y + 10) if len(title) < 3 else (60, y - 10) 
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

    def daytime(self):
        config = self.config
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

if __name__ == "__main__":
    flag_dump, flag_config, flag_svg = False, False, False
    temp_dir = '/tmp/'
    if 'dump' in sys.argv:
        flag_dump = True
        sys.argv.remove('dump')
    elif 'config' in sys.argv:
        flag_config = True
        sys.argv.remove('config')
    elif 'svg' in sys.argv:
        flag_svg = True
        sys.argv.remove('svg')
        
    # Use custom settings    
    if len(sys.argv) > 1:
        a = sys.argv[1]
    else:
        a = "settings.xml"

    config = read_config(setting=a, user=user_setting)
    entries = get_source(config['url'], entries=config['entries'])
    if  flag_dump == True:
        #import pprint
        print(json.dumps(config, indent=4, ensure_ascii=False))
        for entry in entries:
            print(json.dumps(entry, indent=4, ensure_ascii=False))
        exit(0)
    elif flag_config == True:
        print(json.dumps(config, indent=4, ensure_ascii=False))
        exit(0)
        
    filelist = list()  
    for n, entry in enumerate(entries, 1):
        p = WordProccessing(config=config, entry=entry)
        svg = p.svg()
        if flag_svg == True:
            print(svg)
            exit(0)
        img_blob = p.png(svg=svg)
        with Image(blob=img_blob) as img:
            img.format = 'png'
            fdir = '/tmp/'
            fname = 'KindleNewsStation_'
            pngfile = '/tmp/' + fname + str(n) + '.png'
            flatten_pngfile = fname + 'flatten_' + str(n) + '.png'
            filelist.append(flatten_pngfile)
            flatten_pngfile = fdir + flatten_pngfile
            img.save(filename=pngfile)
            t.sleep(1)
            out = Popen(['convert', '-rotate', '+90', '-flatten', pngfile, flatten_pngfile])
            #display(img)
        img.close()
    
    # Create env
    with open('/tmp/KindleNewsStation.env', 'w') as f:
        kindle = config['kindle']
        f.write('duration={}\n'.format(kindle['duration']))
        f.write('repeat={}\n'.format(kindle['repeat']))
        f.write('display_reset="{}"\n'.format(kindle['display_reset']))
        f.write('filelist="{}"\n'.format(' '.join(filelist)))
        f.write('post_run="{}"\n'.format(kindle['post_run']))
    f.close()






