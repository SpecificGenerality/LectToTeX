# -*- coding: utf-8 -*-
"""
Created on Mon Aug  7 08:25:08 2017

@author: Justin Yan
"""

class Transcript(object):
    '''
    Wrapper class for string fed into BeautifulSoup
    '''
    def __init__(self,  file_in):
        #HTML text from file
        self.text = """
        """
        with open(file_in, encoding = 'utf-8') as file:
            for line in file:
                self.text = self.text + line
    