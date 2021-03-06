#!/usr/bin/python -tt

import argparse
import sqlite3
from urlparse import urlparse
import urllib2
import urllib
import json

class SmartRedirectHandler(urllib2.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        newreq = urllib2.HTTPRedirectHandler.redirect_request(self, req, fp, code, msg, headers, newurl)
        print '>> REDIRECT INFO <<'
        print_response(req.get_full_url(), code, headers)
        print '>> REDIRECT HEADERS DETAILS <<'
        for header in headers.items():
            check_header(header)
        print '>> REDIRECT MISSING HEADERS <<'
        missing_headers(headers.items())
        return newreq

def print_database(headers):
    conn = sqlite3.connect('hsecscan.db')
    cur = conn.cursor()
    cur.execute('SELECT * FROM headers')
    col_names = [cn[0] for cn in cur.description]
    for row in cur:
        col_index = 0
        if (headers == False) | (row[6] == 'Y'):
            for cel in row:
                print col_names[col_index] + ':', cel
                col_index += 1
            print '\n'
    cur.close()
    conn.close()

def print_response(url, code, headers):
    print 'URL:', url
    print 'Code:', code
    print 'Headers:'
    for line in str(headers).splitlines():
        print '', line
    print ''

def check_header(header):
    conn = sqlite3.connect('hsecscan.db')
    cur = conn.cursor()
    t = (header[0],)
    if allheaders:
        cur.execute('SELECT "Header Field Name", "Reference", "Security Description", "Security Reference", "Recommendations", "CWE", "CWE URL" FROM headers WHERE "Header Field Name" = ? COLLATE NOCASE', t)
    else:
        cur.execute('SELECT "Header Field Name", "Reference", "Security Description", "Security Reference", "Recommendations", "CWE", "CWE URL" FROM headers WHERE "Enable" = "Y" AND "Header Field Name" = ? COLLATE NOCASE', t)
    col_names = [cn[0] for cn in cur.description]
    for row in cur:
        col_index = 0
        for cel in row:
            if col_names[col_index] == 'Header Field Name':
                print col_names[col_index] + ':', cel, '\nValue: ' + header[1]
            else:
                print col_names[col_index] + ':', cel
            col_index += 1
        print ''
    cur.close()
    conn.close()

def missing_headers(headers):
    conn = sqlite3.connect('hsecscan.db')
    cur = conn.cursor()
    cur.execute('SELECT "Header Field Name", "Reference", "Security Description", "Security Reference", "Recommendations", "CWE", "CWE URL" FROM headers WHERE "Required" = "Y"')
    col_names = [cn[0] for cn in cur.description]
    header_names = [name[0] for name in headers]
    for row in cur:
        if row[0].lower() not in (name.lower() for name in header_names):
            col_index = 0
            for cel in row:
                print col_names[col_index] + ':', cel
                col_index += 1
            print ''
    cur.close()
    conn.close()

def scan(url, redirect, useragent, postdata, proxy):
    request = urllib2.Request(url.geturl())
    request.add_header('User-Agent', useragent)
    request.add_header('Origin', 'http://hsecscan.com')
    if postdata:
        request.add_data(urllib.urlencode(postdata))
    if proxy:
        proxy = urllib2.ProxyHandler({'http': proxy, 'https': proxy})
        if redirect:
            opener = urllib2.build_opener(proxy, SmartRedirectHandler())
        else:
            opener = urllib2.build_opener(proxy)
        urllib2.install_opener(opener)
    else:
        if redirect:
            opener = urllib2.build_opener(SmartRedirectHandler())
            urllib2.install_opener(opener)
    response = urllib2.urlopen(request)
    print '>> RESPONSE INFO <<'
    print_response(response.geturl(), response.getcode(), response.info())
    print '>> RESPONSE HEADERS DETAILS <<'
    for header in response.info().items():
        check_header(header)
    print '>> RESPONSE MISSING HEADERS <<'
    missing_headers(response.info().items())

def check_url(url):
    url_checked = urlparse(url)
    if ((url_checked.scheme != 'http') & (url_checked.scheme != 'https')) | (url_checked.netloc == ''):
        raise argparse.ArgumentTypeError('Invalid %s URL (example: https://www.hsecscan.com/path).' % url)
    return url_checked

def main():
    parser = argparse.ArgumentParser(description='A security scanner for HTTP response headers.')
    parser.add_argument('-P', '--database', action='store_true', help='Print the entire response headers database.')
    parser.add_argument('-p', '--headers', action='store_true', help='Print only the enabled response headers from database.')
    parser.add_argument('-u', '--URL', type=check_url, help='The URL to be scanned.')
    parser.add_argument('-R', '--redirect', action='store_true', help='Print redirect headers.')
    parser.add_argument('-U', '--useragent', metavar='User-Agent', default='hsecscan', help='Set the User-Agent request header (default: hsecscan).')
    parser.add_argument('-d', '--postdata', metavar='\'POST data\'', type=json.loads, help='Set the POST data (between single quotes) otherwise will be a GET (example: \'{ "q":"query string", "foo":"bar" }\').')
    parser.add_argument('-x', '--proxy', help='Set the proxy server (example: 192.168.1.1:8080).')
    parser.add_argument('-a', '--all', action='store_true', help='Print details for all response headers. Good for check the related RFC.')
    args = parser.parse_args()
    if args.database == True:
        print_database(False)
    elif args.headers == True:
        print_database(True)
    elif args.URL:
        global allheaders
        allheaders = args.all
        scan(args.URL, args.redirect, args.useragent, args.postdata, args.proxy)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()