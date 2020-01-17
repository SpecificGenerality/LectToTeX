# -*- coding: utf-8 -*-
"""
Created on Thu Aug  3 22:33:18 2017

@author: Justin Yan
regex - powerful way to match/find things
The Happiness Hypothesis
"""

"""
THINGS TO FIX:
    spacefactor $\LaTeX$ error
    keychars messed up when last char
    bolded + italicized text

THINGS TO ADD:

    color: default = False
        more emoji support
"""
import argparse
import os, os.path
import sys
# for scraping MathJax
from bs4 import BeautifulSoup
from bs4.element import NavigableString
from transcript import Transcript
#for web-scraping images
import urllib.request
from urllib.error import URLError
import shutil

text_formatters = {'b': r'\textbf{', 'i': r'\textit{'}
spacing_formatters =  {r'br': ' ', r'nobr':  ' '}

keychars = {'_': r'\_', '#': r'\#', '$': r'\$', '^': r'\^{}', '&': r'\&',
            '~': r'\~{}', '%', r'\%'}

keychars_first = {'{': r'\{', '}': r'\}', '\\': r'\textbackslash'}

begin_commands = {r'\begin{align*}': r'\begin{align}', r'\begin{eqnarray*}': r'\begin{eqnarray}'}
end_commands = {r'\end{align*}': r'\end{align}', r'\end{eqnarray*}': r'\end{eqnarray}'}
block_commands = {r'\begin{align*}': r'\end{align*}',  r'\begin{eqnarray*}': r'\end{eqnarray*}'}
counter = 1
week_number = 0

def lect_to_TeX(args):
    # file to be read
    file_in = args.file_in
    file_out = args.file_out
    image_path = args.image_out
    file_name = args.file_name

    #instantiate Transcript object
    the_transcript = Transcript(file_in)
    #access string instance var containing HTML text
    transcript_text = the_transcript.text
    #BeautifulSoup object allows easier traverse of HTML text
    soup = BeautifulSoup(transcript_text, 'html.parser')

    O = open(file_out + file_name, 'w')

    transcribe_preamble(soup, O, image_path)

    transcribe_msgs(soup, O, image_path)

    O.write(r'\end{document}')
    counter = 0

def transcribe_preamble(soup_in, file_out, image_path):

    def transcribe_packages(file_out):
        #process the package imports
        file_out.write(r'\documentclass[11pt, twoside, letterpaper]{article}' + '\n')
        file_out.write(r'\usepackage{amssymb, amsmath}' +' \n')
        file_out.write(r'\usepackage[]{microtype}' + '\n')
        file_out.write(r'\usepackage{parskip}' + '\n')
        file_out.write(r'\usepackage[letterpaper]{geometry}' + '\n')
        file_out.write(r'\usepackage{graphicx}' + '\n')
        file_out.write(r'\usepackage[space]{grffile}' + '\n')
        file_out.write(r'\usepackage{float}' + '\n')
        file_out.write(r'\usepackage{tikzsymbols}')
        file_out.write(r'\graphicspath{ {' + image_path + '} }' + '\n')
        file_out.write(r'\usepackage{hyperref}' + '\n')
        file_out.write(r'\hypersetup{' + '\n' + r'colorlinks=true,' + '\n' + r'linkcolor=blue,' + r'filecolor=magenta' + '\n' + 'urlcolor=cyan' + '\n}')

    def transcribe_title(soup_in, file_out):
        global week_number
        #process the class name
        class_tag = soup_in.find('h1')

        #process the lecture name
        lecture_title = soup_in.find('h3').contents[0]

        week_number = lecture_title.split('(')[0].strip()

        #process the instructor's name
        instructor_name = class_tag.next_sibling.next_sibling.contents[0]

        #write the lecture title
        file_out.write(r"\title{" + lecture_title + "\\\\")
        file_out.write(class_tag.contents[0].strip() + "}\n\n")
        file_out.write(r'\author{' + instructor_name + '}' +  '\n')

    def transcribe_start(file_out):
        #start the document
        file_out.write(r'\begin{document}' + '\n')

        #write the lecture title
        file_out.write(r'\maketitle' + '\n')

    transcribe_packages(file_out)
    transcribe_title(soup_in, file_out)
    transcribe_start(file_out)

def transcribe_msgs(soup_in, file_out, image_path):
    #list holds all of the HTML blocks containing user and  moderator messages
    message_blocks = soup_in.find_all(name='div', attrs={'class':['grid-transcript-row']})

    #print the messages
    for tag in message_blocks:

        #print the username
        name_tag = tag.find(name='span', attrs={'class':'name'})
        name = name_tag.contents[0].contents[0]
        for char in  name:
            if char in keychars.keys():
                name = name[0: name.index(char)] + keychars[char] + name[name.index(char) + 1:]
        #boldface the usernames
        file_out.write(r"\textbf{" + name + "} \quad{} ")

        #find the message tag in the message block
        msg_tag = tag.find(name='div', attrs={'class':'msg text'})

        #write the message to output file
        process_message(msg_tag, file_out, image_path)
        file_out.write('\n\n')

#write all user and mod messages to the output file
def process_message(msg_tag, file_out, image_path):

    #writes the messages that do not contain LaTeX math
    def process_text(child_tag, file_out):
        #write strings with no special formatting
        if isinstance(child_tag, NavigableString):
            #replace all special laTeX characters with their plain text versions
            for elt in keychars_first.keys():
                if elt in child_tag:
                    child_tag = child_tag.replace(elt, keychars_first[elt])
            for elt in keychars.keys():
                if elt in child_tag:
                    child_tag = child_tag.replace(elt, keychars[elt])
            file_out.write(child_tag)
        #write bolded, italicized, etc text
        elif child_tag.name in text_formatters.keys():
            file_out.write(text_formatters[child_tag.name])
            for grandchild in child_tag.descendants:
                process_text(grandchild, file_out)
            file_out.write(r'}')
        #process line breaks and shit
        elif child_tag.name in spacing_formatters.keys():
            file_out.write(spacing_formatters[child_tag.name])
            for grandchild in child_tag.descendants:
                process_text(grandchild, file_out)

    #writes messages containing LaTeX math
    def process_math(child_tag, file_out):
        found = False
        #filter the relevant tags
        if child_tag.name == 'script' and "math/tex; mode=display" in child_tag.attrs.values():
            #fix the different block tags (align, center, etc)
            for key in block_commands.keys():
                if key in child_tag.contents[0]:
                    found = True
                    file_out.write(begin_commands[key] + child_tag.contents[0][len(key):-len(block_commands[key])] + end_commands[block_commands[key]] + '\n')
            #add delimiters for inline math
            if not found:
                file_out.write(r'\[' + child_tag.contents[0] +  r'\]' + '\n')
        elif child_tag.name == 'script' and 'type' in child_tag.attrs.keys() and child_tag.attrs['type'] == 'math/tex':
            file_out.write(r'$' + child_tag.contents[0] + r'$')

    def process_image(child_tag, file_out, image_path):

        global counter, week_number
        #save_dir = os.path.abspath('lectures_images')
        #extract the image link from its tag
        url = child_tag.attrs['src']
        if 'http' not in url:
            url = 'http:' + url
        #extract the image name from the url
        file_name = week_number + '-' + str(counter) +  '.jpg'
        #complete file path for saved image
        full_path = os.path.join(image_path, file_name)
        # Download the file from `url` and save it locally under `file_name`:
        with urllib.request.urlopen(url) as response, open(full_path, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)

        #write LaTeX tags for image
        file_out.write(r'\begin{figure}[H]' + '\n')
        file_out.write(r'\centering' + '\n')
        file_out.write(r'\includegraphics[width=0.5\textwidth]{' + file_name + r'}' + '\n')
        file_out.write(r'\end{figure}' + '\n')
        counter +=  1

    def process_link(child_tag, file_out):
        link =  child_tag.attrs['href']
        name =  child_tag.contents[0]
        file_out.write(r'\href{' + link + '}{' + name + '}')

    #loop through all children of the msg_text tag and write to file
    for child in msg_tag.contents:
        #try-except deals with annoying UnicodeEncodeErrors because can't process > <
        try:
            #if the tag contains just text
            if isinstance(child, NavigableString) or child.name in text_formatters:
                process_text(child, file_out)
            #if the tag contains an image
            elif child.name == 'img':
                print('image found')
                try:
                    process_image(child, file_out, image_path)
                except URLError:
                    print(child)
                    continue
            elif child.name == 'div' and child.attrs == {'class': ['latex']} and child.contents[0].name == 'img':
                print('image found')
                try:
                    process_image(child.contents[0], file_out, image_path)
                except URLError:
                    print(child)
                    continue
            #if the tag contains a link
            elif child.name ==  'a' and ['bbcode_url'] in child.attrs.values():
                print('link found')
                process_link(child, file_out)
            #everything else we're interested in is math typeset
            else:
                process_math(child, file_out)
        except UnicodeEncodeError:
            continue

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Converts HMTL files contain MathJax into LaTeX')
    parser.add_argument('--file_in', help="the lecture's HTML file to parse", required=True)
    parser.add_argument('--file_out', help='the directory to write files to')
    parser.add_argument('--image_out', help='the directory to write images to')
    parser.add_argument('--file_name', help='the name of the file to write')
    args = parser.parse_args()

    lect_to_TeX(args)