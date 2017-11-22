# -*- coding: utf-8 -*-
"""
Created on Tue Aug 15 11:01:27 2017

@author: Justin Yan
"""
"""
Process document
    def Process page title
    def Process problem title
        -find tag w/name=div and  "problem-header" in tag.attrs.values()
        -loop through w/contents
            - if NavigableString
                -if "Problem" in NavigableString
                    - write to file
    def Process problem text
        -find all problem blocks w/soup.find_all(name="div" and class="problem-block")
        -find start tag
            -name='div' and attrs={'class': 'body'}
        -process all elements
            -loop through tag.contents[0]
                -if NavigableString, write to file
                -elif math in img tag, write tag['alt'] to file
    def process hints
        - find name = 'div', attrs = {'class':['problem-box', 'hint']}
        - loop through all contents and write to file
    def Process problem solution
        -find all solution blocks
            -soup.find_all(name='div', attrs={'class': ['problem-block', 'solution']})
        -write solution header to file
        -process problem text
            -find start tag
                -either use above method or just loop
            -process all elements same as above
    
"""


from bs4 import BeautifulSoup
from transcript import Transcript
from bs4.element import NavigableString
import os, os.path
#for web-scraping images
import urllib.request
import shutil
from urllib.error import URLError

spacing_formatters =  {r'br': r'  ', r'nobr':  r'  '}
keychars = {'_': r'\_', '#': r'\#', '$': r'\$', '^': r'\^{}', '&': r'\&',
            '~': r'\~{}'}
which_format =  ''
keychars_first = {'{': r'\{', '}': r'\}', '\\': r'\textbackslash'}
text_formatters = {'b': r'\textbf{', 'i': r'\textit{'}
begin_commands = {r'\begin{align*}': r'\begin{align}', r'\begin{eqnarray*}': r'\begin{eqnarray}'}
end_commands = {r'\end{align*}': r'\end{align}', r'\end{eqnarray*}': r'\end{eqnarray}'}
block_commands = {r'\begin{align*}': r'\end{align*}',  r'\begin{eqnarray*}': r'\end{eqnarray*}'}

counter = 1
week_number = 0
def homework_html_to_LaTeX(file_in, soln = False):
    global week_number
    the_homework = Transcript(file_in)
    the_homework_text = the_homework.text
    soup = BeautifulSoup(the_homework_text, 'html.parser')
    print('souped up!')
    
    if not soln:
        file_name = file_in.strip().split('/')[9][0:-8] + "LaTeXnosoln.txt"
        file_out = open('C:/Users/Justin Yan/Documents/Development/Python/AoPSCleanScript/AoPSCleanScript/homework_LaTeX/' + file_name, 'w')
        print('File opened for writing')
    else:
        file_name = file_in.strip().split('/')[9][0:-8] + "LaTeXwithsoln.txt"
        file_out = open('C:/Users/Justin Yan/Documents/Development/Python/AoPSCleanScript/AoPSCleanScript/homework_LaTeX/' + file_name, 'w')
        print('File opened for writing')
    
    week_number = file_name.split('HTML')[0]
    transcribe_preamble(soup, file_out)
    #process the problem body
    transcribe_problems(soup,  file_out, soln)
    
    file_out.write('\end{document}')
def transcribe_preamble(soup_in, file_out):
    #adds the package imports to the document
    def transcribe_packages(file_out):
        file_out.write(r'\documentclass[11pt, twoside, letterpaper]{article}' + '\n')
        file_out.write(r'\usepackage{amssymb, amsmath}' +' \n')
        file_out.write(r'\usepackage[]{microtype}' + '\n')
        file_out.write(r'\usepackage{parskip}' + '\n')
        file_out.write(r'\usepackage[letterpaper]{geometry}' + '\n')
        file_out.write(r'\usepackage{graphicx}' + '\n')
        file_out.write(r'\usepackage[space]{grffile}' + '\n')
        file_out.write(r'\usepackage{float}' + '\n')
        file_out.write(r'\usepackage{tikzsymbols}' + '\n')
        file_out.write(r'\title{' + 'Week 1 Homework} \n')
        file_out.write(r'\graphicspath{ {C:/Users/Justin Yan/Documents/Development/Python/AoPSCleanScript/AoPSCleanScript/homework_images/} }' + '\n')
    
    #starts the LaTeX document
    def transcribe_start(file_out):
    #start the document
        file_out.write(r'\begin{document}' + '\n')
    
        #write the lecture title
        file_out.write(r'\maketitle' + '\n')
    
    #write the package imports
    transcribe_packages(file_out)
    print('packages imports written')
    
    #write the document start and title tags
    transcribe_start(file_out)
    print('document start commands written')
    
def transcribe_problems(soup_in, file_out, soln = False):
    
    #list of all the problem header tags
    header_tags = soup_in.find_all(name = 'div', attrs = {'class': ['problem-header']})
    
    
    
    def process_text(elt, file_out):
        global which_format
        if isinstance(elt, NavigableString):
            for key in keychars_first.keys():
                if key in elt:
                    elt = elt.replace(key, keychars_first[key])
            for key in keychars.keys():
                if key in elt:
                    elt = elt.replace(key, keychars[key])
            file_out.write(elt)
        #write bolded, italicized, etc text
        elif elt.name in text_formatters.keys():
            which_format = elt.name
            file_out.write(text_formatters[elt.name])
            for grandchild in elt.descendants:
                process_text(grandchild, file_out)
            file_out.write(r'}')
            #process line breaks and shit
        elif elt.name in spacing_formatters.keys():
            file_out.write(spacing_formatters[elt.name])
        elif elt.name == 'img' and 'alt' in elt.attrs.keys():
            if which_format == 'i':
                file_out.write('} ' + elt['alt'] +  r'\textit{')
            elif which_format ==  'b':
                file_out.write('} ' + elt['alt'] +  r'\textbf{')
                    
    def process_math(elt, file_out):
        found = False
        for key in block_commands.keys():
            if key in elt['alt']:
                found = True
                file_out.write(begin_commands[key] + elt['alt'][len(key):-len(block_commands[key])] + end_commands[block_commands[key]] + '\n')
        if not found:
            if elt.attrs['class'] == ['asy-image']:
                global counter, week_number
                print('asymptote image found')
                save_dir = os.path.abspath('homework_images')
                #extract the image link from its tag
                url = elt.attrs['src']
                if 'http' not in url:
                    url = 'http:' + url
                #extract the image name from the url
                file_name = week_number + '-' + str(counter) +  '.jpg'
                #complete file path for saved image
                full_path = os.path.join(save_dir, file_name)
        
                # Download the file from `url` and save it locally under `file_name`:
                with urllib.request.urlopen(url) as response, open(full_path, 'wb') as out_file:
                    shutil.copyfileobj(response, out_file)
                    
                    #write LaTeX tags for image
                file_out.write(r'\begin{figure}[H]' + '\n')
                file_out.write(r'\centering' + '\n')
                file_out.write(r'\includegraphics[width=0.5\textwidth]{' + file_name + r'}' + '\n')
                file_out.write(r'\end{figure}' + '\n')
                counter +=  1
            else:   
                file_out.write(elt['alt'])
            
    def process_problem(problem_tag, file_out):
        print('process_problem reached')
        start_tag =  problem_tag.find_next(name='div', attrs={'class': 'body'})
        
        for elt in start_tag.contents:
            if isinstance(elt, NavigableString) or elt.name in text_formatters or elt.name in spacing_formatters:
                #replace all special laTeX characters with their plain text versions
                process_text(elt, file_out)
            elif elt.name ==  'img' and 'alt' in elt.attrs.keys():
                process_math(elt, file_out)
            elif elt.name == 'span':
                for subelt in elt.contents:
                    if isinstance(subelt, NavigableString):
                        file_out.write(subelt)
                    elif subelt.name == 'img' and 'alt' in subelt.attrs.keys():
                        process_math(subelt, file_out)
                        
        file_out.write('\n \n')
            
    def process_solution(solution_tag, file_out):
        print('process solution reached')
        file_out.write(r'\textbf{Solution:}' + '\n \n')
        
        start_tag =  solution_tag.find_next(name='div', attrs={'class': 'body'})
        
        for elt in start_tag.contents:
            if isinstance(elt, NavigableString) or elt.name in text_formatters or elt.name in spacing_formatters:
                #replace all special laTeX characters with their plain text versions
                process_text(elt, file_out)
            elif elt.name ==  'img' and 'alt' in elt.attrs.keys():
                process_math(elt, file_out)
            elif elt.name == 'span':
                for subelt in elt.contents:
                    if isinstance(subelt, NavigableString):
                        file_out.write(subelt)
                    elif subelt.name == 'img' and 'alt' in subelt.attrs.keys():
                        process_math(subelt, file_out)
                        
        file_out.write('\n \n')

    def process_hint(hint_tag, file_out): 
        print('process hint reached')
        for elt in hint_tag.contents:
            if isinstance(elt, NavigableString):
                continue
            elif elt.name == 'div':
                for subelt in  elt.contents:
                    if isinstance(subelt, NavigableString) or subelt.name in text_formatters or subelt.name in spacing_formatters:
                        #replace all special laTeX characters with their plain text versions
                        process_text(subelt, file_out)
                    elif subelt.name ==  'img' and 'alt' in subelt.attrs.keys():
                        process_math(subelt, file_out)
                    elif subelt.name == 'span':
                        for subsubelt in subelt.contents:
                            if isinstance(subsubelt, NavigableString):
                                file_out.write(subsubelt)
                            elif subsubelt.name == 'img' and 'alt' in subsubelt.attrs.keys():
                                process_math(subsubelt, file_out)
                                
        file_out.write('\n \n')
    
    def process_submission(submission_tag, file_out):
        print('process student submission reached')
        
        file_out.write(r'\textbf{Your response:}' + '\n \n ')
        start_tag =  submission_tag.find_next(name='div', attrs={'class': 'body'})
        
        for elt in start_tag.contents:
            if isinstance(elt, NavigableString) or elt.name in text_formatters or elt.name in spacing_formatters:
                #replace all special laTeX characters with their plain text versions
                process_text(elt, file_out)
            elif elt.name ==  'img' and 'alt' in elt.attrs.keys():
                try:
                    process_math(elt, file_out)
                except URLError:
                    print('failed to grab image')
            elif elt.name == 'span':
                for subelt in elt.contents:
                    if isinstance(subelt, NavigableString):
                        file_out.write(subelt)
                    elif subelt.name == 'img' and 'alt' in subelt.attrs.keys():
                        try:
                            process_math(subelt, file_out)
                        except URLError:
                            print('failed to grab image')
                            
        file_out.write('\n\n ' + r'\textbf{Comments: }')
        
        comments_tag = start_tag.find_next(name = 'div', attrs = {'class': 'body'})
    
        for elt in comments_tag.contents:
            if isinstance(elt, NavigableString) or elt.name in text_formatters or elt.name in spacing_formatters:
                #replace all special laTeX characters with their plain text versions
                process_text(elt, file_out)
            elif elt.name ==  'img' and 'alt' in elt.attrs.keys():
                try:
                    process_math(elt, file_out)
                except URLError:
                    print('failed to grab image')
            elif elt.name == 'span':
                for subelt in elt.contents:
                    if isinstance(subelt, NavigableString):
                        file_out.write(subelt)
                    elif subelt.name == 'img' and 'alt' in subelt.attrs.keys():
                        try:
                            process_math(subelt, file_out)
                        except URLError:
                            print('failed to grab image')
                            
        file_out.write('\n\n')
    #program loop
    for tag in header_tags:
        #write the NavigableString containing the correct problem number and part number (if available)
        for elt in tag.contents:
            if isinstance(elt, NavigableString) and "Problem" in elt:
                print('problem header found')
                file_out.write(r"\textbf{" + elt.strip() + r"} " + "\n \n")
                break
                
        start_tag = tag.find_next(name = 'div', attrs = {'class': 'problem-body'})
        #loop through the entire problem body to locate problem text, solution text, and hint text (if available)
        for elt in start_tag.descendants:
            if isinstance(elt, NavigableString):
                continue
            elif elt.name == 'div' and elt.attrs == {'class': [r'problem-block', 'first']}:
                print('problem text tag found')
                process_problem(elt, file_out)
            elif elt.name == 'div' and elt.attrs == {'class': [r'problem-block', 'solution']}:
                print('solution text tag found')
                if soln:
                    process_solution(elt, file_out)
            elif elt.name == 'div'and elt.attrs == {'class': [r'problem-box', 'hint']}:
                print('hint tag found')
                process_hint(elt, file_out)
            elif elt.name == 'div' and elt.attrs == {'class': [r'problem-box', r'gray', r'free-response-submission']}:
                print('student submission found')
                if soln:
                    process_submission(elt, file_out)
        file_out.write('\n \n')

                
                
                