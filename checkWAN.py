#!/usr/bin/env python
#
# Script to check for the Internet Address and log/report it
# Should run through a LaunchAgent/Daemon
# written by Chris G. Sellers (cgseller@gmail.com)
#
#

import os
import urllib2
import smtplib
import argparse
import json
import sys
from syslog import syslog as slog


__author__ = 'Chris G. Sellers'
__verson__ = '0.0.1'

class checkWAN(object):
    '''
    check WAN address and return attributes
    '''
    def __init__(self):
        '''
        uses json - a candidate for templating no doubt
        '''
        self.vetter = 'http://api.ipify.org?format=json'
        self.newip = None
        self.existing = None
        self.datafile = '/var/tmp/checkWAN.ip'
        self.authpass = None
        self.sender = args.sender or None
        self.receiver = args.receiver or None

    def fetchaddress(self):
        '''
        reach out and get the publc IP(4) address
        '''
        try:
            theurl = urllib2.urlopen(self.vetter, timeout=30)
            resp = json.loads(theurl.read())
            self.newip = resp['ip'] or None
        except Exception as E:
            _msg = 'Unable to connecto {}:{}'.format(
                self.vetter, E)
            print(_msg)
            slog(_msg)

    def currentIP(self):
        '''
        what is the current expected ip
        so we can compare it to the discovered
        if different, notify
        '''
        try:
            with open('/var/tmp/checkWAN.ip', 'rb') as f:
                self.existing = f.readlines(20)
        except IOError as IOE:
            if os.path.isfile(self.datafile):
                _msg = ('ERROR - existing IP file exists but can not open it'
                        ' - check permissions/format : {} : {}'.format(
                            self.datafile, IOE))
            else:
                self.existing = None
                _msg = ('Existing IP empty/malformed - assumed None')
            print(_msg)
            slog(_msg)

    def compareIPs(self):
        '''
        compare the IPs to see if the new is different from the existing
        '''
        notify = False
        if self.newip is not self.existing:
            notify = True
            _msg = ('IP address changed '
                    'OLD: {} : '
                    'NOW: {}'.format(self.existing, self.newip))
            try:
                with open(self.datafile, 'wb') as f:
                    f.write(self.newip)
            except IOerror as e:
                _msg = ('unable to write {} : {}'.format(self.datafile, e))
                print _msg
                slog(_msg)
        else:
            _msg = ('No IP Change Detected')

        slog(_msg)
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
        except Exception as SMTPE:
            _msg = ('error sending SMTP message : {}'
                    '- contents : {}'.format(SMTPE, smtp_message))
            print _msg
            slog(_msg)

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
        args = parser.parse_args()
    except Exception as e:
        print e

    ipcheck = checkWAN()
    if args.datafile:
        ipcheck.datafile = args.datafile

    if args.provider:
        ipcheck.vetter = args.provider

    if args.password:
        ipcheck.authpass = args.password

    if sys.version[:3] < '2.6':
        raise RuntimeWarning("Version not 2.7+")

    ipcheck.fetchaddress()
    ipcheck.currentIP()
    (notify, message) = ipcheck.compareIPs()
    if notify:
        ipcheck.sendmessage(message)


if __name__ == '__main__':
    main()

