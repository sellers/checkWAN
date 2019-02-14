#!/usr/bin/env python
"""
 Script to check for the Internet Address and log/report it
 Should run through a LaunchAgent/Daemon/Upstart/etc
 written by Chris G. Sellers (cgseller[at]gmail.com)
 code written to by python3 and python2 friendly
"""

try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser
try:
    from urllib2 import (urlopen,
                         URLError,
                         Request)
except ImportError:
    from urllib.request import (urlopen,
                                Request)
    from urllib.error import URLError
import io
import os
import sys
import json
import syslog
import logging
import smtplib
import argparse

from syslog import syslog as slog
from base64 import b64decode
from email.mime.text import MIMEText


__author__ = 'Chris G. Sellers'
__verson__ = '0.0.3'

class CheckWAN(object):
    """
    check WAN address and return attributes
    """

    def __init__(self, sender=None, receiver=None, level=0):
        """
        create an object to obtain and compare the IP address
        initially written for ipify.org, but maybe needs to be changed
        to handle multiple APIs (ReST) and learn the return format
        """
        self.vetter = 'http://api.ipify.org?format=json'
        self.newip = None
        self.existing = None
        self.datafile = '/var/tmp/checkWAN.ip'
        self.authpass = None
        self.receiver = receiver
        self.sender = sender
        self.loglevel = level

    def __repr__(self):
        """
        define representation here
        """
        print("""
              vetting system: {}
              existing ip : {}
              sender: {}
              receiver: {}
              datafile: {}
              """.format(self.vetter, self.existing, self.sender,
                         self.receiver, self.datafile))

    def config(self):
        """
        config file for passwords and access information
        default to /etc/check-wan.cfg
        format:
        [ipservice]
        url = http://api.ipify.org?format=json
        [mail]
        from = cgseller@mac.com
        to = cgseller@mac.com
        password = xxxxxyyyyyzzzz=
        """

        getconfig = ConfigParser.ConfigParser()
        try:
            getconfig.readfp(io.open('/etc/check_wan.cfg', 'rt'))
        except IOError as error:
            _msg = ('unable to open config : {}'.format(error))
            slog(syslog.LOG_WARNING, _msg)
            if self.loglevel > 2:
                print(_msg)
        self.sender = getconfig.get('mail', 'from') or None
        self.receiver = getconfig.get('mail', 'to') or None
        self.authpass = b64decode(getconfig.get('mail', 'password')) or None


    def reset(self):
        """
        reset any state
        """
        try:
            os.unlink(self.datafile)
        except OSError as oserr:
            _msg = ('unable to remove data file: {} : {}'.format(self.datafile,
                                                                 oserr))
            slog(syslog.LOG_WARNING, _msg)
            if self.loglevel > 1:
                print(_msg)
        else:
            slog(syslog.LOG_ERR, 'unable to reset')
            if self.loglevel > 0:
                print('unable to reset... {}'.format(self.datafile))

    def fetchaddress(self):
        """
        reach out and get the publc IP(4) address
        """
        count = 0
        try:
            while (self.newip not None) and (count+=1 < 3):
                theurl = urlopen(Request(self.vetter), timeout=30)
                resp = json.loads(str(theurl.read().decode('utf-8')))
                self.newip = resp['ip'] or None
                sleep 3
        except URLError as uee:
            _msg = 'Unable to connect {}:{}'.format(
                self.vetter, uee)
            if self.loglevel > 1:
                print(_msg)
            slog(syslog.LOG_ERR, _msg)
        except Exception as generr:
            _msg = 'No response for IP, internet outage?'

    def current_ip(self):
        """
        what is the current expected ip
        so we can compare it to the discovered
        if different, notify
        """
        try:
            with io.open('/var/tmp/checkWAN.ip', 'rt') as dataf:
                self.existing = dataf.readlines(20)[0]
                _msg = ('existing IP found as {}'.format(self.existing))
        except IOError as ioe:
            if os.path.isfile(self.datafile):
                _msg = ('ERROR - existing IP file exists but can not open it'
                        ' - check permissions/format : {} : {}'.format(
                            self.datafile, ioe))
            else:
                _msg = ('No status file found, assume null')
                self.existing = None
        except IndexError as ierr:
            self.existing = None
            _msg = ('Existing IP empty/malformed - assumed None : {}'
                    .format(ierr))
        if self.loglevel > 1:
            print(_msg)
        slog(syslog.LOG_ERR, _msg)

    def compare_ips(self):
        """
        compare the IPs to see if the new is different from the existing
        """
        notify = False
        if str(self.newip) != str(self.existing):
            notify = True
            _msg = ('IP address changed '
                    'OLD: {}. '
                    'NOW: {}.'.format(self.existing, self.newip))
            if self.loglevel > 1:
                print(_msg)
            try:
                with io.open(self.datafile, 'wt') as dataf:
                    dataf.write(self.newip)
            except IOError as ioe:
                _msg = ('unable to write {} : {}'.format(self.datafile, ioe))
                if self.loglevel > 0:
                    print(_msg)
                slog(syslog.LOG_ERR, _msg)
        else:
            _msg = ('No IP Change Detected')
            if self.loglevel > 2:
                print(_msg)

        slog(syslog.LOG_ERR, _msg)
        return(notify, _msg)

    def sendmessage(self, message):
        """
        send a message to a recipient
        """
        smtp_message = MIMEText("""
                        {}

                        to SSH there, use new IP address
                        """.format(message))
        smtp_message['Subject'] = ('WAN Address changed @ JAZZY Cove {}'
                                   .format(self.newip))
        smtp_message['From'] = self.sender
        smtp_message['To'] = self.receiver

        if self.loglevel > 1:
            print('  attempting to send email....')
        try:
            smtpobj = smtplib.SMTP('smtp.gmail.com', 587)
            smtpobj.ehlo()
            smtpobj.starttls()
            smtpobj.ehlo()
            smtpobj.login(self.sender, self.authpass)
            smtpobj.sendmail(self.sender,
                             self.receiver,
                             smtp_message.as_string())
            smtpobj.close()
            if self.loglevel > 1:
                print('  sent {} to {}.'.format(smtp_message, self.receiver))
        except smtplib.SMTPConnectError as smtp_err:
            _msg = ('error sending SMTP message : {}'
                    '- contents : {}'.format(smtp_err, smtp_message))
            if self.loglevel > 2:
                print(_msg)
            slog(syslog.LOG_ERR, _msg)

def logdebug(info, level=0):
    """
    logger method to handle debug prints or logging
    3 = print everything
    2 = debug as debug messages
    1 = warning
    """
    if level > 2:
        print(info)
        logging.debug(info)
    else:
        logging.error(info)

def main():
    """
    make a call out to an external name service to ip provider and return
    what the calling external IP(4) address is
    """

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
        parser.add_argument('-v', '--verbose',
                            help="""Verbosity: -v - errors;
                                    -v -v - debugging;
                                    -v -v - everything
                                 """,
                            nargs='*',
                            action='append',
                            default=[])
        parser.add_argument('-c', '--config',
                            help='config file, default = ./check_wan.cfg',
                            default='./check_wan.cfg')
        args = parser.parse_args()
        if len(sys.argv) < 2:
            parser.print_usage()
            sys.exit(1)
    except argparse.ArgumentError as arge:
        logdebug("argparse error : {}".format(arge), len(args.verbose) or None)
    verbosity = len(args.verbose) or 0
    if verbosity > 1:
        print("in verbose 2+ mode")

    ipcheck = CheckWAN(args.receiver,
                       args.sender,
                       verbosity)
    ipcheck.config()  # default config information override below
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
    if notify:
        ipcheck.sendmessage(message)


if __name__ == '__main__':
    main()

