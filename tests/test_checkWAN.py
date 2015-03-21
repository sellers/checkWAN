#!/usr/bin/python
#
import unittest
from checkWAN import checkWAN

def getIP(name):
    '''
    unit test for checkWAN
    '''
    return checkWAN(name).ip

class testCheckWAN(unittest.TestCase):
    ''' checkWAN '''
    def test(self):
        self.asertEqual(getIP('127.0.0.1', 'localhost'))
