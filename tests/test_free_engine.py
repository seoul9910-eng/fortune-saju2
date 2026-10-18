import unittest
from engine import get_chart

class TestFreeEngine(unittest.TestCase):
    def base(self,birth,hour='12',minute='0',**kw):
        return get_chart(dict(birth=birth,calendar='solar',hour=hour,minute=minute,gender='남성',**kw))
    def test_lichun_boundary(self):
        before=self.base('20240204','17','20')
        after=self.base('20240204','17','30')
        self.assertEqual((before['year'],before['month']),('癸卯','乙丑'))
        self.assertEqual((after['year'],after['month']),('甲辰','丙寅'))
    def test_known_date(self):
        c=self.base('19920326')
        self.assertEqual((c['year'],c['month'],c['day']),('壬申','癸卯','辛丑'))
    def test_unknown_hour(self):
        self.assertIsNone(self.base('19920326','unknown')['hour'])
    def test_different_day(self):
        self.assertNotEqual(self.base('19920326')['day'],self.base('19920327')['day'])
    def test_invalid_date(self):
        with self.assertRaises(ValueError):self.base('20240230')
if __name__=='__main__':unittest.main()
