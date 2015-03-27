#!/usr/bin/virtual-env python
'''
 Script to check for the Internet Address and log/report it
 Should run through a LaunchAgent/Daemon
 written by Chris G. Sellers (cgseller@gmail.com)
'''

import os
import urllib2
import smtplib
import argparse
import json
import sys
import syslog
import logging
from syslog import syslog as slog


__author__ = 'Chris G. Sellers'
__verson__ = '0.0.1'

class CheckWAN(object):
    '''
    check WAN address and return attributes
    '''

    def __init__(self, sender=None, receiver=None, level=0):
        '''
        create an object to obtain and compare the IP address
        initially written for ipify.org, but maybe needs to be changed
        to handle multiple APIs (ReST) and learn the return format
        '''
        self.vetter = 'http://api.ipify.org?format=json'
        self.newip = None
        self.existing = None
        self.datafile = '/var/tmp/checkWAN.ip'
        self.authpass = None
        self.receiver = receiver
        self.sender = sender
        self.loglevel = level

    def __repr__(self):
        '''
        define representation here
        '''
        print('''
              vetting system: {}
              existing ip : {}
              sender: {}
              receiver: {}
              datafile: {}
              '''.format(self.vetter, self.existing, self.sender,
                         self.receiver, self.datafile))

    def reset(self):
        '''
        reset any state
        '''
        try:
            os.unlink(self.datafile)
        except OSError as oserr:
            _msg = ('unable to remove data file: {} : {}'.format(self.datafile,
                                                                 oserr))
            slog(syslog.LOG_WARNING, _msg)
            print _msg
        else:
            slog(syslog.LOG_ERR, 'unable to reset')

    def fetchaddress(self):
        '''
        reach out and get the publc IP(4) address
        '''
        try:
            theurl = urllib2.urlopen(self.vetter, timeout=30)
            resp = json.loads(theurl.read())
            self.newip = str(resp['ip']) or None
            print self.newip
        except urllib2.URLError as uee:
            _msg = 'Unable to connecto {}:{}'.format(
                self.vetter, uee)
            print _msg
            slog(syslog.LOG_ERR, _msg)

    def current_ip(self):
        '''
        what is the current expected ip
        so we can compare it to the discovered
        if different, notify
        '''
        try:
            with open('/var/tmp/checkWAN.ip', 'rb') as dataf:
                self.existing = dataf.readlines(20)[0]
        except IOError as ioe:
            if os.path.isfile(self.datafile):
                _msg = ('ERROR - existing IP file exists but can not open it'
                        ' - check permissions/format : {} : {}'.format(
                            self.datafile, ioe))
            else:
                self.existing = None
                _msg = ('Existing IP empty/malformed - assumed None')
            print _msg
            slog(syslog.LOG_ERR, _msg)

    def compare_ips(self):
        '''
        compare the IPs to see if the new is different from the existing
        '''
        notify = False
        if str(self.newip) != str(self.existing):
            notify = True
            _msg = ('IP address changed '
                    'OLD: {}. '
                    'NOW: {}.'.format(self.existing, self.newip))
            print _msg
            try:
                with open(self.datafile, 'wb') as dataf:
                    dataf.write(self.newip)
            except IOError as ioe:
                _msg = ('unable to write {} : {}'.format(self.datafile, ioe))
                print _msg
                slog(syslog.LOG_ERR, _msg)
        else:
            _msg = ('No IP Change Detected')

        slog(syslog.LOG_ERR, _msg)
        return(notify, _msg)

    def sendmessage(self, message):
        '''
        send a message to a recipient
        '''
        smtp_message = ("""From:{}
                        To:{}
                        Subject: WAN address changed @home {}

                        {}

                        to SSH home, use new IP address
                        to print to home via IPP type printer, use new IP address and port 1631
                        """.format(self.sender, self.receiver,
                                   self.newip, message))

        try:
            smtpobj = smtplib.SMTP('smtp.gmail.com', 587)
            smtpobj.ehlo()
            smtpobj.starttls()
            smtpobj.ehlo()
            smtpobj.login(self.sender, self.authpass)
            smtpobj.sendmail(self.sender,
                             self.receiver,
                             smtp_message)
            smtpobj.close()
        except smtplib.SMTPConnectError as smtp_err:
            _msg = ('error sending SMTP message : {}'
                    '- contents : {}'.format(smtp_err, smtp_message))
            print _msg
            slog(syslog.LOG_ERR, _msg)

def logdebug(info, level=0):
    '''
    logger method to handle debug prints or logging
    3 = print everything
    2 = debug as debug messages
    1 = warning
    '''
    if level > 2:
        print info
        logging.debug(info)
    else:
        logging.error(info)

def main():
    '''
    make a call out to an external name service to ip provider and return
    what the calling external IP(4) address is
    '''

    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('-f', '--datafile',
                            help='Location to store previous IP')
        parser.add_argument('-p', '--provider',
                            help='check IP service')
        parser.add_argument('-w', '--password',
                            help='sender password')
        parser.add_argument('-s', '--sender',
                            help='sending e-mail address')
        parser.add_argument('-r', '--receiver',
                            help='receiving e-mail address')
        parser.add_argument('-R', '--reset',
                            help='reset eveything')
        parser.add_argument('-n', '--noop', action='store_true',
                            help='do not send email')
        parser.add_argument('-v', '--verbose', help='''Verbosity: v - errors;
                                                        vv - debugging;
                                                        vvv - everything''')
        args = parser.parse_args()
    except argparse.ArgumentError as arge:
        logdebug("argparse error : {}".format(arge), len(args.verbose))
    ipcheck = CheckWAN(args.receiver,
                       args.sender,
                       len(args.verbose))
    if args.datafile:
        ipcheck.datafile = args.datafile

    if args.provider:
        ipcheck.vetter = args.provider

    if args.password:
        ipcheck.authpass = args.password

    if sys.version[:3] < '2.6':
        raise RuntimeWarning("Version not 2.7+")

    ipcheck.fetchaddress()
    ipcheck.current_ip()
    (notify, message) = ipcheck.compare_ips()
    if notify and not __debug__:
        ipcheck.sendmessage(message)


if __name__ == '__main__':
    main()

