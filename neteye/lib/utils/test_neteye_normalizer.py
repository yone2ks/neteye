import unittest
from neteye_normalizer import normalize_mac_address, normalize_mask, normalize_speed, normalize_duplex
import netaddr

print(normalize_mac_address("00:1A:2B:3C:4D:5E"))
print(normalize_mac_address("00-1A-2B-3C-4D-5E"))
print(normalize_mac_address("001A.2B3C.4D5E"))

print(normalize_mask("24"))
print(normalize_mask("16"))
print(normalize_mask("255.255.0.0"))    
#class TestNeteyeNormalizer(unittest.TestCase):

    #def test_normalize_mac(self):
        #self.assertEqual(normalize_mac("00:1A:2B:3C:4D:5E"), netaddr.EUI("00:1A:2B:3C:4D:5E").mac)
        #self.assertEqual(normalize_mac("00-1A-2B-3C-4D-5E"), netaddr.EUI("00-1A-2B-3C-4D-5E").mac)

    #def test_normalize_mask(self):
        #self.assertEqual(normalize_mask("24"), "255.255.255.0")
        #self.assertEqual(normalize_mask("16"), "255.255.0.0")

    #def test_normalize_speed(self):
        #self.assertEqual(normalize_speed("1000 Mbps"), "1000Mbps")
        #self.assertEqual(normalize_speed(" 100 Mbps "), "100Mbps")

    #def test_normalize_duplex(self):
        #self.assertEqual(normalize_duplex(" full "), "full")
        #self.assertEqual(normalize_duplex("half"), "half")

    #def test_normalize_mtu(self):
        #self.assertEqual(normalize_mtu("1500"), 1500)
        #self.assertEqual(normalize_mtu("9000"), 9000)

#if __name__ == '__main__':
    #unittest.main()