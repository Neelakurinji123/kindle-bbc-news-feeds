#!/usr/bin/env python3
# encoding=utf-8
# -*- coding: utf-8 -*-

class format:
    def __init__(self, encoding, height, width, font, _svg):
        self.encoding = encoding
        self.height = height
        self.width = width
        self.font = font
        self._svg = _svg
        
    def svg(self):
        a = f'''<?xml version="1.0" encoding="{self.encoding}"?>
<svg xmlns="http://www.w3.org/2000/svg" height="{self.height}" width="{self.width}" version="1.1" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 450 600" preserveAspectRatio="xMinYMin meet">
<g font-family="{self.font}">
{self._svg}
</svg>\n'''
        return a

# Reguler font
class text:
    def __init__(self, anchor, fontsize, x, y, v, stroke=None, font_family=None):
        self.anchor = anchor
        self.fontsize = fontsize
        self.x = x
        self.y = y
        self.v = v
        self.stroke = stroke
        self.font_family = font_family

    def svg(self):
        if not self.stroke == None:
            return f'<text style="text-anchor:{self.anchor};" font-size="{self.fontsize}px" x="{self.x}" y="{self.y}" stroke="{self.stroke}" fill="{self.stroke}">{self.v}</text>\n'
        else:
            return f'<text style="text-anchor:{self.anchor};" font-size="{self.fontsize}px" x="{self.x}" y="{self.y}">{self.v}</text>\n'
    def svg_font(self):
        a = f'<g font-family="{self.font_family}">\n'
        a += self.svg()
        a += '</g>'
        return a
        

# Bold font
class text2:
    def __init__(self, anchor, fontweight, fontsize, x, y, v):
        self.anchor = anchor
        self.fontweight = fontweight
        self.fontsize = fontsize
        self.x = x
        self.y = y
        self.v = v

    def svg(self):
        return '<text style="text-anchor:{};" font-weight="{}" font-size="{}px" x="{}" y="{}">{}</text>\n'.\
               format(self.anchor, self.fontweight, self.fontsize, self.x, self.y, self.v)


class circle:
    def __init__(self, cx, cy, r, stroke, width, fill):
        self.cx = cx
        self.cy = cy
        self.r = r
        self.stroke = stroke
        self.width = width
        self.fill = fill

    def svg(self):
        return '<circle cx="{}" cy="{}" r="{}" stroke="{}" stroke-width="{}" fill="{}"/>\n'.\
               format(self.cx, self.cy, self.r, self.stroke, self.width, self.fill)


class line:
    def __init__(self, x1, x2, y1, y2, style):
        self.x1 = x1
        self.x2 = x2
        self.y1 = y1
        self.y2 = y2
        self.style = style

    def svg(self):
        return '<line x1="{}" x2="{}" y1="{}" y2="{}" style="{}"/>\n'.\
                format(self.x1, self.x2, self.y1, self.y2, self.style)


class transform:
    def __init__(self, matrix, obj):
        self.matrix = matrix
        self.obj = obj

    def svg(self):
        return '<g transform="matrix{}">{}</g>\n'.format(self.matrix, self.obj)


class polyline:
    def __init__(self, points, style):
        self.points = points
        self.style = style

    def svg(self):
        return '<polyline points="{}" style="{}"/>\n'.format(self.points, self.style)


class rect:
    def __init__(self, x, y, width, height, style):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.style = style

    def svg(self):
        return '<rect x="{}" y="{}" width="{}" height="{}" style="{}"/>\n'.format(self.x, self.y, self.width, self.height, self.style)


class path:
    def __init__(self, d, style):
        self.d = d
        self.style = style

    def svg(self):
        return '<path d="{}" style="{}"/>\n'.format(self.d, self.style)

