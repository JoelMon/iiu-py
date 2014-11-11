#!/usr/bin/env python3

"""
    Copyright 2014 Joel Montes de Oca <JoelMontes01@gmail.com>

    This file is part of iiu.

    iiu is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    iiu is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with iuu. If not, see <http://www.gnu.org/licenses/>.

"""

import argparse
import datetime
import http.client
import os
import time
import urllib.request

version = '1.0 alpha'
app = 'iiu'

def main():
    """

    iiu is a command line tool to aid system administrators when deploying
    or maintaining web servers. iiu is used to check if a web site is
    available from outside of your own network. It accomplishes this by using
    the freely available isitup.org API. iiu's output is customizable
    making it simple to incorporate it into a script.

    """

    parser = argparse.ArgumentParser(description='{0} checks to see if a website is \
                                                 accessible outside of your network.'.format(app))
    parser.add_argument('-r',
                        '--return-only',
                        metavar='opt',
                        type=str, nargs='+',
                        choices=['c', 'd', 'p', 'i', 's', 't', 'l'],
                        help='Only outputs options selected.'
                        )

    subparsers = parser.add_subparsers(title='--return-only options')
    subparsers.add_parser('c', help='Output the current date and time')
    subparsers.add_parser('d', help='Output the domain name of the site being checked')
    subparsers.add_parser('p', help='Output the port used')
    subparsers.add_parser('i', help='Output the IP address of the website')
    subparsers.add_parser('s', help='Output the status code returned by the server')
    subparsers.add_parser('t', help='Output the response time')
    subparsers.add_parser('l', help="Don't output the option's lable")

    parser.add_argument('-u',
                        '--url',
                        required=True,
                        help='The URL to check'
                        )

    parser.add_argument('-s',
                        '--simple',
                        action='store_true',
                        help='Simplified output [default]'
                        )

    parser.add_argument('-f',
                        '--fancy',
                        action='store_true',
                        help='Multiline printing with more information'
                        )

    parser.add_argument('-i',
                        '--ip',
                        action='store_true',
                        help='Returns only the IP address of the URL'
                        )

    parser.add_argument('-v',
                        '--version',
                        action='version',
                        version='{0} {1}'.format(app, version),
                        help='Print version'
                        )

    args = parser.parse_args()

    try:
        url = url_sanity(args.url)
    except TypeError:
        print('[ERROR: -u missing] The -u [URL] argument must be used.')
        return 1

    simple = args.simple
    fancy = args.fancy
    ip = args.ip
    return_only = args.return_only

    if simple:
        print_simple(url)
    elif fancy:
        print_fancy(url)
    elif ip:
        print_ip(url)
    elif return_only:
        label_state = True

        if 'l' in return_only:
            if len(return_only) == 1:
                print('ERROR: Option l can not be used alone.')
                return 1

            label_state = False
            return_only.remove('l')
            print_return_only(url, return_only, label_state)
        else:
            print_return_only(url, return_only, label_state)
    else:
        print_simple(url)

    return 0


def clean_list(lst):
    """Cleans the returned list to remove the trailing ','

    isitup.org returns a string with commas (','), when the string
    is converted to a list, the list elements has a ',' appended
    to the end of each element except for the last. This function
    removes the trailing comma from each element if it exists.

    Example of dirty list:
    ['Domain.com,', '80,', '1,', '255.255.255.255,', '301,', '0.104']

    ARG:
        takes lst as the list with the trailing ','

    Returns:
        returns a new list without the trailing ','

    """

    cleaned_list = []

    for element in lst:
        if element[-1:] == ',':
            cleaned_list.append(element[:-1])
    else:
        cleaned_list.append(element)

    return cleaned_list


def print_fancy(url):
    """Prints data in using multilines.

    Takes the URL which the user would like to check and displays it on the
    screen using multilines. The reason for this print option is to be pleaseing
    to the eyes of the user, it's not meant to be used by scripts.

    data_list scheme:
        ['domain', 'port',
         'status code', 'response ip','response code',
          response time']]

    ARG:
        url - The URL which the user would like to check.

    """

    data_list = (request_url(url))
    status = response_status(data_list)
    if status[1][4] == 'NULL':  # Keeps http.client.responses from running
        response_code = 'NULL'  # if status[1][4] is 'NULL' which causes
    else:                       # a KeyError.
        response_code = http.client.responses[int(status[1][4])]


    os.system('clear')  # Send 'clear' to terminal. Will cause an error in Windows
    print('')
    print('                  _  _' )
    print('                 (_)(_)')
    print('                  _  _  _   _')
    print('                 | || || | | |')
    print('                 | || || |_| |')
    print('                 |_||_| \__,_|')
    print('')
    print('')
    print('                The site is {}'.format(status[0]))
    print('---------------------------------------------------')
    print('        Domain ------------ {}'.format(data_list[0]))
    print('        IP address -------- {}'.format(data_list[3]))
    print('        Response time ----- {}'.format(data_list[5]))
    print('        HTTP code --------- {0} {1}'.format(data_list[4], response_code))
    print('---------------------------------------------------')
    print('        Current time: {}'.format(time_stamp()))
    print('---------------------------------------------------')
    print('')
    return 0


def print_ip(url):
    """Prints only the IP address of the website.

    Only prints the IP address of the URL entered. No time-stamp is
    provided in this mode. If time-stamp is needed then the '-r i'
    should be used. This function is meant to be used as a shortcut
    to getting an IP address.

    ARGS:
        url the URL of the site to check

    """

    data_list = (request_url(url))
    status = response_status(data_list)

    if status[0] == 'NONRESPONSIVE':
        print('Domain: {} is down.'.format(status[1][0]))
    elif status[0] == 'DOWN':
        print('{}'.format(status[1][3]))
    elif status[0] == 'UP':
        try:                                   # status[1][3] can be NULL which causes a ValueError
            print ('{}'.format(status[1][3]))
        except ValueError:
            print ('{}'.format(status[1][3]))

    return 0


def print_return_only(url, args, label_state):
    """Returns only the information the user requests.

    The print_return_only() takes url, args, and
    label_state as arguments and then prints on the
    screen the information the user wants.

    data_list scheme:
        ['domain', 'port', 'status code', 'response ip',
         'response code', response time']

    args_dic scheme:
        {user_options : [order_index,
                         string to display,
                         loc of data in data_list
                         ]

    ARG:
        url         This is the URL the user wishes to check
        args        The options chosen by the user to display
        label_state Whether the user wants to have the
                    information displayed with labels.

    """

    data_list = (request_url(url))
    status = response_status(data_list)
    valid_args = ['c', 's', 'd', 'p', 'i', 't']
    args = list(set(args))  # Removes duplicate options
    user_lst = []
    args_dic = {'c' : ['0', '{}', time_stamp()],
                'd' : ['1', 'domain={}', data_list[0]],
                'i' : ['2', 'ip={}', data_list[3]],
                'p' : ['3', 'port={}', data_list[1]],
                's' : ['4', 'status_code={}', data_list[4]],
                't' : ['5', 'response_time={}', data_list[5]]
                }

    for option in args:
        if option not in valid_args:
            print('[ERROR] Option {} is not valid.'.format(option))
            print('')
            print(' +---------------------------------------+')
            print(' | The following options are valid       |')
            print(' |                                       |')
            print(' | c - print a time-stamp                |')
            print(' | d - return the domain name            |')
            print(' | i - return the IP address             |')
            print(' | p - return the port                   |')
            print(' | t - return the response time          |')
            print(' | s - return the status code            |')
            print(' | l - return options without labels     |')
            print(' | Example: $ iiu -r d t -u domain.com   |')
            print(' +---------------------------------------+')
            print('')
            return 1

    if status[0] != 'UP':
        if 'c' in args:
            print('{0} - {1} is down'.format(time_stamp(), data_list[0]))
        else:
            print('{0} is down'.format(data_list[0]))
    else:
        if label_state:  # Prints with time-stamp
            for user_opt in args:
                user_lst.append(args_dic[user_opt][0] + ' ' +
                                args_dic[user_opt][1].format(args_dic[user_opt][2]))  # Unsordered
            print('%s' % ' '.join(map(str, sort_order(user_lst))))  # Sorts and prints the user's list of options
        else:
            for user_opt in args:  # Prints without time-stamp
                user_lst.append(args_dic[user_opt][0] + ' ' +
                                args_dic[user_opt][2])  # Unsordered
            print('%s' % ' '.join(map(str, sort_order(user_lst))))  # Sorts and prints the user's list of options

    return 0

def print_simple(url):
    """Prints a simple output.

    Only requires a URL to function. The output is kept simple and consistant,
    can't be customized.

    The data_list consists of two nested lists. The first list is the status
    of the website, is it up down, etc, as determined by response_status().
    The second list contains the data returned from isitup.org.

    data_list scheme:
        [[status_of_site], ['domain', 'port',
         'status code', 'response ip','response code',
          response time']]

    """

    data_list = (request_url(url))
    status = response_status(data_list)

    if status[0] == 'NONRESPONSIVE':
        print('{0} Domain: {1} is down'.format(time_stamp(), status[1][0]))
    elif status[0] == 'DOWN':
        print('{0} Domain {1}, returned an IP but is down'.format(time_stamp(), status[1][0]))
    elif status[0] == 'UP':
        try:
            response_code = http.client.responses[int(status[1][4])]  # Returns HTTP code's meaning
            print ('{0} Domain: {1} ({2}) Response Time: {3} HTTP: {4} {5}'.format(time_stamp(),
                                                                                   status[1][0],
                                                                                   status[1][3],
                                                                                   status[1][5],
                                                                                   status[1][4],
                                                                                   response_code
                                                                                    ))
        except ValueError:
            print ('{0} Domain: {1} ({2}) Response Time: {3} HTTP: {4}'.format(time_stamp(),
                                                                               status[1][0],
                                                                               status[1][3],
                                                                               status[1][5],
                                                                               status[1][4]
                                                                                ))


def sort_order(lst):
    """Takes a list of user choosen options and returns it in a perdictable order.

    Since dictionaries do not have a perdictable order, this function takes
    the user's options choosen and orders it in a perdectable manner. It does
    this by looking at the first number in the first list element. After the
    list is ordered, it returns the ordered list with the prefixed number
    stirped out (ex opt[2:]). The number prefix is hard coded in the
    print_return_only() fuction in the args_dic dictionary.

    ARG:
        lst The list of choosen options by the user in random order

    RETURN:
        ordered_lst The new list in a perdictable order

    """

    ordered_lst = []
    sorted_lst = []

    sorted_lst = sorted(lst)

    for opt in sorted_lst:
        ordered_lst.append(opt[2:])
    return ordered_lst


def request_url(url):
    """Request body of the URL entered.

    Requests the URL and returns the body of the page from http://isitup.org.
    It also cleans it using the clean_list(lst) function. Everything gets
    returned as a string.

    ARG:
        url: the url that will be sent to http://isitup.org

    Returns:
        returns the body of the http://isitup.org

    """

    headers = {'User-Agent' : app + '/' + version}

    url = 'http://isitup.org/' + url + '.txt'
    req = urllib.request.Request(url, None, headers)
    response = urllib.request.urlopen(req)
    body = response.read()
    body = body.decode('utf-8')
    body = clean_list(body.split())  # Takes body, lists it, and cleans it.
    return body


def response_status(lst):
    """Returns the status of the website along with the lst in a tuple.

    Takes lst and checks to see if the website is one of the three states,
    then return the state of the site plus the list that was passed into
    response_status(lst).

    States:

        NONRESPONSIVE - Site does not return an IP address
        DOWN          - Site is down but returns an IP
        UP            - Site is up

    ARG:
        lst - The response from http:isitup.org after it
              has been cleaned.

    RETURNS:
        A tuple containing the state of the site as a string
        and the original list passed in.

    """

    if lst[0] == lst[3]:
        return ('NONRESPONSIVE', lst)
    elif lst[5] == 'NULL' and lst[4] == 'NULL':
        return ('DOWN', lst)
    else:
        return ('UP',lst)


def time_stamp():
    """Produces a time stamp.

    When called, it creates a time stamp and returns it.

    Not sure if this function works as expectd
    under other platforms.

    """

    current_time = time.time()
    human_readable = datetime.datetime.fromtimestamp(current_time).strftime('%Y-%m-%d %H:%M:%S')
    return human_readable


def url_sanity(url):
    """Strips invalid prefixes from url.

    isitup.org does not accept a URLs with a 'http://' or http:
    prefix. This function checks to see if the user entered the prefix
    and strips it from the url if so. 'https://' and 'https:' are also
    stripped.

    ARGS:
        takes url as the URL the user entered

    RETURNS:
        returns url with the invalid prefixes removed if found

    """

    if url[:7] == 'http://':
        return url[7:]
    elif url[:8] == 'https://':
        return url[8:]
    elif url[:5] == 'http:':
        return url[5:]
    elif url[:6] == 'https:':
        return url[6:]
    else:
        return url


if __name__ == '__main__':
    main()
