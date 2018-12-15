# -*- coding: utf-8 -*-
"""
Go to Google Bookmarks: https://www.google.com/bookmarks/

On the bottom left, click "Export bookmarks": https://www.google.com/bookmarks/bookmarks.html?hl=en

After downloading the html file, run this script on it to get the addresses

This script is based on https://gist.github.com/endolith/3896948
"""

import sys

from lxml.html import document_fromstring
from geopy.geocoders import Nominatim
import simplekml
import json
from urllib2 import urlopen
from urllib import urencode
import re
import time

filename = r'GoogleBookmarks.html'

def main():
    with open(filename) as bookmarks_file:
        data = bookmarks_file.read()
    
    geolocator = Nominatim()

    kml = simplekml.Kml()

    lst = list()
    
    # Hacky and doesn't work for all of the stars:
    lat_re = re.compile('markers:[^\]]*latlng[^}]*lat:([^,]*)')
    lon_re = re.compile('markers:[^\]]*latlng[^}]*lng:([^}]*)')
    coords_in_url = re.compile('\?q=(-?\d{,3}\.\d*),\s*(-?\d{,3}\.\d*)')
    
    doc = document_fromstring(data)
    for element, attribute, url, pos in doc.body.iterlinks():
        if 'maps.google' in url:
            description = element.text or ''
            print description.encode('UTF8')
            
            if coords_in_url.search(url):
                # Coordinates are in URL itself
                latitude = coords_in_url.search(url).groups()[0]
                longitude = coords_in_url.search(url).groups()[1]
            else:
                # Load map and find coordinates in source of page
                try:
                    sock = urlopen(url.replace(' ', '+').encode('UTF8'))
                except Exception, e:
                    print 'Connection problem:'
                    print repr(e)
                    print 'Waiting 2 minutes and trying again'
                    time.sleep(120)
                    sock = urlopen(url.replace(' ', '+').encode('UTF8'))
                content = sock.read()
                sock.close()
                time.sleep(3) # Don't annoy server
                try:
                    latitude = lat_re.findall(content)[0]
                    longitude = lon_re.findall(content)[0]
                except IndexError:
                    try:
                        lines = content.split('\n')  # --> ['Line 1', 'Line 2', 'Line 3']
                        for line in lines:
                            if re.search('cacheResponse\(', line):
                                splitline = line.split('(')[1].split(')')[0] + '"]'
                                # in the future we can extract the coordinates from here
                                null = None
                                values = eval(splitline)
                                print values[8][0][1]
                                longitude = str(values[0][0][1])
                                latitude = str(values[0][0][2])
                                continue
                    except IndexError:
                        print '[Coordinates not found]'
                        continue
                    print
            
            print latitude, longitude
            try:
    			location = geolocator.reverse(latitude+", "+longitude)
    			print(location.address)
            except ValueError:
                print '[Invalid coordinates]'
            print
            kml.newpoint(name=description, coords=[(float(longitude), float(latitude))])
            lst.append({'latitude': latitude,
                       'longitude': longitude,
                       'name': description,
                       'url': url.encode(encoding='utf-8', errors='replace'),
                       'address': location.address.encode(encoding='utf-8', errors='replace') if location else 'error'})

            # this is here because there's a tendancy for this script to fail part way through...
            # so at least you can get a partial result
            kml.save("GoogleBookmarks.kml")
            with open('GoogleBookmarks.json', mode='w') as listdump:
                listdump.write(json.dumps(lst))
        sys.stdout.flush()

    kml.save("GoogleBookmarks.kml")
    with open('GoogleBookmarks.json', mode='w') as listdump:
        listdump.write(json.dumps(lst))

if __name__ == '__main__':
    main()
