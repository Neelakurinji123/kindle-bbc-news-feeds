#!/usr/bin/env python3
# encoding=utf-8
# -*- coding: utf-8 -*-

# Written by : krishna@hottunalabs.net
# Update     : 26 May 2024 

import json, os, sys, re, io
from pathlib import Path
import time as t
from datetime import datetime, date
import zoneinfo
from urllib.request import urlopen
import feedparser
import xml.etree.ElementTree as ET
from subprocess import Popen, PIPE
from PIL import ImageFont
from wand.image import Image
from wand.drawing import Drawing
from wand.display import display
from cairosvg import svg2png
import qrcode

# Working dir
this_file = os.path.realpath(__file__)
path = Path(this_file).parents[0]
os.chdir(str(path))

import SVGtools 

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
            config['layout']['dark_mode'] = service.find('dark_mode').text
    # user config
    if not user == None:
        tree = ET.parse(user)
        root = tree.getroot()
        for service in root.findall('service'):
            if service.get('name') == 'user':
                config['timezone'] = service.find('timezone').text if service.find('timezone') is not None else 'UTC'
                #config['lat'] = float(service.find('lat').text) if service.find('lat').text is not None else 0
                #config['lon'] = float(service.find('lon').text) if service.find('lon').text is not None else 0
                config['lat'] = float(service.find('lat').text) if service.find('lat') is not None else 0
                config['lon'] = float(service.find('lon').text) if service.find('lon') is not None else 0
    else:
        config['timezone'] = 'UTC'
        config['lat'] = '0'
        config['lon'] = '0'
    
    if config['timezone'] == 'local':
        config['now'] = int(datetime.now().timestamp())
    else:
        tz = zoneinfo.ZoneInfo(config['timezone'])
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
        self.dark_mode = config['layout']['dark_mode']
        self.tz = zoneinfo.ZoneInfo(config['timezone']) if not config['timezone'] == 'local' else None
        
    def png(self, svg=None):
        layout = self.config['layout']
        zone = self.config['timezone']
        now = self.config['now']
        # News clip
        png_clip = self.img_clip()
        # Logo png
        png_logo = self.img_logo()
        # QR code
        img = qrcode.make(self.link)
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
                bg_img.composite(fg_img, left=20, top=285)
            fg_img.close()
            # Logo image
            with Image(blob=png_logo) as fg_img:
                bg_img.composite(fg_img, left=58, top=500)
            fg_img.close() 
            img_blob = bg_img.make_blob('png')
        bg_img.close()
        # Dark mode
        if config['layout']['dark_mode'] == 'True' or (config['layout']['dark_mode'] == 'Auto' and self.daytime() == 'night'):
            print('darkmode')
            with Image(blob=img_blob) as img:
                with img.clone() as i:
                     i.negate(True,"all_channels")
                     i_blob = i.make_blob('png')
                i.close()
            img.close()
            img_blob = i_blob
            
        return img_blob
        
    def img_clip(self):
        layout = self.config['layout']
        clip = urlopen(self.media_thumbnail)
        try:
            with Image(file=clip) as img:                    
                with img.clone() as i:
                    i.resize(560, 315) # 16:9
                    if layout['img_effect'] == 0:  # grey
                        i.transform_colorspace('gray')
                    if layout['img_effect'] == 1:  # Color Threshold
                        i.color_threshold(start='#333', stop='#cdc')
                    elif layout['img_effect'] == 2:  # Auto Threshold ('triangle'))
                        i.auto_threshold(method='triangle')
                    elif layout['img_effect'] == 3: # Adaptive Threshold
                        i.transform_colorspace('gray')
                        i.adaptive_threshold(width=16, height=16,
                            offset=-0.08 * i.quantum_range)
                    elif layout['img_effect'] == 4: # Ordered Dither (Circles 6x6)
                        i.transform_colorspace('gray')
                        i.ordered_dither('c6x6b')
                    elif layout['img_effect'] == 5: # Random Threshold
                        i.transform_colorspace('gray')
                        i.random_threshold(low=0.3 * i.quantum_range,
                             high=0.6 * i.quantum_range)
                    elif layout['img_effect'] == 6: # Range Threshold (soft)
                        i.transform_colorspace('gray')
                        white_point = 0.9 * i.quantum_range
                        black_point = 0.2 * i.quantum_range
                        delta = 0.05 * i.quantum_range
                        i.range_threshold(low_black=black_point - delta,
                            low_white=white_point - delta,
                            high_white=white_point + delta,
                            high_black=black_point + delta)
                    elif layout['img_effect'] == 7: # black & white
                        i.transform_colorspace('gray')
                        i.background_color = 'white'
                        i.alpha_channel = False
                        i.threshold(threshold=0.25)
                    elif layout['img_effect'] == 8: # Sketch
                        i.transform_colorspace('gray')
                        i.sketch(0.5, 0.0, 98.0)
                    elif layout['img_effect'] == 9: # Noise
                        i.noise("laplacian", attenuate=1.0)
                        i.transform_colorspace('gray')
                        
                    png_blob = i.make_blob('png')
        finally:
            clip.close()
        return png_blob

    def img_logo(self):
        logo_image = self.config['logo_image']
        timezone = self.config['timezone']
        lat = self.config['lat']
        lon = self.config['lon']
        state = self.daytime() if not timezone == 'GMT' and not lat == 0 and not lon == 0 else 'night'
        with Image(filename=logo_image) as img:
            with img.clone() as i:
                    i.transform_colorspace('gray')
                    #i.transform(resize='240x120>')
                    if state == 'day':
                        i.level(black=0.0, white=None, gamma=2.5)
                    png_blob = i.make_blob('png')
        return png_blob        
        
    def svg(self):
        layout = self.config['layout']
        zone = self.config['timezone']
        now = self.config['now']
        body = str()
        if layout['paper_layout'] == 'landscape':
            width, height = 800, 600
        else:
            width, height = 600, 800
        encoding = layout['encoding']
        font = layout['font']
        # maintenant
        if self.config['timezone'] == 'local':
            maintenant = (str.lower(datetime.fromtimestamp(now).strftime('%a, %d %b %H:%M')))
        else:
            maintenant = (str.lower(datetime.fromtimestamp(now, self.tz).strftime('%a, %d %b %H:%M')))
        # published
        utc = zoneinfo.ZoneInfo('UTC')
        self.published.append(utc)
        d = datetime(*self.published)
        time = d.timestamp()
        da = int((now - time) / 86400)
        hr = int((now - time) / 3600)
        mi = int((now - time) % 60)
        if da == 0 and hr == 0 and mi == 0:
            ago = 'now'
        elif da == 0 and hr == 0 and mi == 1:
            ago = 'now' 
        elif da == 0 and hr == 0:
            ago = f'{mi} mins ago'
        elif da == 0 and hr == 1:
            ago = 'an hour ago'
        elif da == 0:
            ago = f'{hr} hrs ago'
        elif da == 1:
            ago = 'a day ago'
        else:
            ago = f'{da} days ago'       
        body += SVGtools.text('start', '30', 20, 40, f'created at {maintenant}').svg()
        body += SVGtools.text('end', '30', 780, 40, ago).svg()
        body += '</g>\n'
        style = 'stroke:rgb(128,128,128);stroke-width:1px;'
        body += SVGtools.line(x1=0, x2=800, y1=50, y2=50, style=style).svg()  
        kw1 = {'rows': layout['title_rows'], 'row_length': layout['title_row_length'], 'font': layout['font'], 
                    'font_size': layout['title_font_size'], 'min_sp': layout['title_font_space'], 'y_padding': layout['title_y_padding']}
        title = self.wordwrap(paragraph=self.title, **kw1)
        kw2 = {'rows': layout['summary_rows'], 'row_length': layout['summary_row_length'], 'font': layout['font'],
                    'font_size': layout['summary_font_size'], 'min_sp': layout['summary_font_space'], 'y_padding': layout['summary_y_padding']}
        summary = self.wordwrap(paragraph=self.summary, **kw2)
        # svg text: title
        (x, y) = (50, 105) if (len(title) == 3 and len(summary) >= 3) else (50, 120)
        a, y = self.text_proccessing(x=x, y=y, paragraph=title, **kw1)
        body += a
        # svg text: summary
        (x, y) = (60, y + 10) if len(title) < 3 else (60, y - 10) 
        a, y = self.text_proccessing(x=x, y=y, paragraph=summary, **kw2)
        body += a
        # svg text: category
        body += SVGtools.text('start', '16', 5, 595, f'category: {config["category"]}', font_family=font).svg_font()
        s = SVGtools.format(encoding=encoding, height=height, width=width, font=font, _svg=body).svg()
        return s

    def text_proccessing(self, x, y, rows, row_length, font, font_size, min_sp, paragraph, y_padding, **kw):
        f = ImageFont.truetype(font, font_size)
        row = 1
        _x = x
        a = f'<g font-family="{font}">\n'
        for t in paragraph:
            if len(t) > 2 and not len(paragraph) == row:
                _sp = int((row_length - f.getlength(''.join(t))) / (len(t) - 1))
                for s in t:
                    a += SVGtools.text(anchor='start', fontsize=font_size, x=_x, y=y, v=s).svg()
                    _x += int(f.getlength(s)) + _sp
            else:
                for s in t:
                    a += SVGtools.text(anchor='start', fontsize=font_size, x=_x, y=y, v=s).svg()
                    _x += int(f.getlength(s)) + min_sp
            _x = x
            y += y_padding
            row += 1                      
        return a + '</g>\n', y
        
    def wordwrap(self, rows, row_length, font, font_size, min_sp, paragraph, y_padding, **kw):
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
        lat = self.config['lat'] if 'lat' in self.config else None
        lon = self.config['lon'] if 'lon' in self.config else None
        zone = self.config['timezone']
        now = self.config['now']
        try:
            from astral import LocationInfo
            from astral.sun import sun
            offset = datetime.now(self.tz).utcoffset().seconds
            city, region = zone.split('/')
            location = LocationInfo(city, region, zone, lat, lon)
            s = sun(location.observer, date=date.today(), tzinfo=self.tz)
            _sunrise, _sunset = s['sunrise'], s['sunset']
            sunrise, sunset = int(_sunrise.timestamp()), int(_sunset.timestamp())
            if sunrise >= now or sunset <= now:
                state = 'night'
            else:
                state = 'day'
            return state
        except:
            return None

def main(config, flag_dump, flag_config, flag_svg, flag_png, flag_display):
    entries = get_source(config['url'], entries=config['entries'])
    if not entries == list(): s = entries[0]['title']
    # breaking news
    if config['breaking_news'] == True:
        if not re.search('breaking', s, re.IGNORECASE):
            exit(0)
    if  flag_dump == True:
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
            # Image clip
            with Image(blob=p.img_clip()) as fg_img:
                # image ratio: (16:9)
                img.composite(fg_img, left=(800 - 560), top=(600 - 315))
            fg_img.close()
            img.alpha_channel_types = 'flatten'
            img.rotate(90)
            img.format = 'png'
            fname = 'KindleNewsStation_flatten_'
            flatten_pngfile = fname + str(n) + '.png'
            filelist.append(flatten_pngfile)
            img.save(filename='/tmp/' + flatten_pngfile)
            t.sleep(1)
            if flag_display == True:
                display(img)
                if n == len(entries):
                    exit(0)
        img.close()
    if flag_png == True:
        exit(0)
    # Display PNGs on kindle
    kindle = config['kindle']
    duration = int(kindle['duration']) * 60
    repeat = int(kindle['repeat'])
    display_reset = kindle['display_reset']
    post_run = kindle['post_run']
    kindleIP = '192.168.2.2'
    cmd = f'''`ssh root@{kindleIP} 'pidof powerd'` 
if [ "$p" != '' ]; then
    ssh root@{kindleIP} "/etc/init.d/powerd stop"
    ssh root@{kindleIP} "/etc/init.d/framework stop"
fi'''
    while repeat >= 0:
        repeat -= 1
        for flatten_pngfile in filelist:
            out = Popen([cmd], shell=True, stdout=PIPE, stderr=PIPE).wait()
            cmd = f'scp /tmp/{flatten_pngfile} root@{kindleIP}:/tmp'
            out = Popen([cmd], shell=True, stdout=PIPE, stderr=PIPE).wait()
            if display_reset == True:
                cmd = f'ssh root@{kindleIP} \"cd /tmp; /usr/sbin/eips -c\"'
                out = Popen([cmd], shell=True, stdout=PIPE, stderr=PIPE).wait()
            cmd = f'ssh root@{kindleIP} \"cd /tmp; /usr/sbin/eips -g {flatten_pngfile}\"'
            out = Popen([cmd], shell=True, stdout=PIPE, stderr=PIPE).wait()
            t.sleep(duration)
    if not post_run == str():
        out = Popen([post_run], shell=True, stdout=PIPE, stderr=PIPE).wait()

if __name__ == "__main__":
    flag_dump, flag_config, flag_svg, flag_png, flag_display = False, False, False, False, False
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
    elif 'png' in sys.argv:
        flag_png = True
        sys.argv.remove('png')
    elif 'display' in sys.argv:
        flag_display = True
        sys.argv.remove('display')
        
    # Use custom feed setting   
    if len(sys.argv) > 1:
        a = sys.argv[1]
    else:
        a = "setting.xml"
    # User setting
    user_setting = 'config/user.xml'
    config = read_config(setting=a, user=user_setting)
    main(config, flag_dump, flag_config, flag_svg, flag_png, flag_display)
    
