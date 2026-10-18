import unittest
from datetime import datetime
from engine import get_chart, solar_from_input, KST, solar_longitude, get_near_jie

class SajuTests(unittest.TestCase):
    def c(self,birth,hour='12',minute='0',**kw):
        return get_chart({'birth':birth,'hour':hour,'minute':minute,**kw})
    def test_known_lichun_2024(self):
        before=self.c('20240204','17','20');after=self.c('20240204','17','30')
        self.assertEqual((before['year'],before['month']),('癸卯','乙丑'))
        self.assertEqual((after['year'],after['month']),('甲辰','丙寅'))
        self.assertEqual(before['day'],after['day'])
    def test_known_lichun_2025(self):
        self.assertEqual(self.c('20250203','23','00')['year'],'甲辰')
        self.assertEqual(self.c('20250203','23','20')['year'],'乙巳')
    def test_lunar_new_year(self):
        self.assertEqual(solar_from_input('20240101','lunar',False).isoformat(),'2024-02-10')
        self.assertEqual(self.c('20240210')['day'],self.c('20240101',calendar='lunar')['day'])
    def test_2023_leap_second_month(self):
        self.assertEqual(solar_from_input('20230201','lunar',True).isoformat(),'2023-03-22')
        with self.assertRaises(ValueError):solar_from_input('20230101','lunar',True)
    def test_different_births(self):
        a=self.c('19920326');b=self.c('19920327')
        self.assertNotEqual(a['day'],b['day'])
        self.assertNotEqual(a['pillars'],b['pillars'])
    def test_hour_pillars(self):
        a=self.c('19920326','11');b=self.c('19920326','13')
        self.assertNotEqual(a['hour'],b['hour'])
        self.assertEqual(self.c('19920326','unknown')['hour'],None)
        self.assertEqual(self.c('19920326','23')['hour'][1],'子')
    def test_jie_month_boundary(self):
        a=self.c('20240305','10');b=self.c('20240306','10')
        self.assertNotEqual(a['month'],b['month'])
    def test_luck_gender(self):
        a=self.c('19920326',gender='남성');b=self.c('19920326',gender='여성')
        self.assertNotEqual(a['luck'][0]['pillar'],b['luck'][0]['pillar'])
    def test_invalid_date(self):
        with self.assertRaises(ValueError):self.c('20240230')
    def test_years(self):
        with self.assertRaises(ValueError):self.c('19500101')
if __name__=='__main__':unittest.main()
