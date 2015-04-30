#!/usr/bin/python
#
import unittest
from .. check_wan import CheckWAN

#def getIP(name):
#    '''
#    unit test for checkWAN
#    '''
#    return checkWAN(name).ip

class testCheckWAN(unittest.TestCase):
    ''' checkWAN '''
    def test_getIP(self):
        check = CheckWAN()
        check.newip = '127.0.0.1'
        ip = check.current_ip()
        self.assertEqual('localhost', ip)

    def test_config(self):
        pass

    def test_sendmessage(self):
        check = CheckWAN()
        check.newip = '0.0.0.0'
        check.config()
        check.sendmessage('check_wan sendmessage passed')
       
if __name__ == '__main__':
    unittest.main()
