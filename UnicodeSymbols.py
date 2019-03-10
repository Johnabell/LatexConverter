"""
This passes the unicode symbol file to generate a dictionary of latex commands to unicode
symbols. 


Author: John Bell
Email: bell.john.andrew@gmail.com
"""

import csv
import os
from collections import namedtuple
import re


latex_spaces = [
    (r'\,', ('02006', r' ', 'mathspace')),
    (r'\:', ('02005', r' ', 'mathspace')),
    (r'\;', ('02004', r' ', 'mathspace')),
    (r'\ ', ('02003', r' ', 'mathspace')),
    (r'\qquad', ('02001', r' ', 'mathspace')),
    (r'\quad', ('02001', '\u2001', 'mathspace'))
    ]
symbol_file_name = 'unimathsymbols.txt'


def get_symbols():
    current_path = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(current_path, symbol_file_name)
    Line = namedtuple('Line', ['unicode', 'chr', 'latex','unimath', 'cls','cat','req','comment'])
    Symbol = namedtuple('Symbol', ['unicode', 'char', 'cat'])
    symbols = {}
    tex = re.compile(r'\\[^,\s]*')
    
    with open(file_path) as f:
        reader = csv.reader(f, delimiter = '^')
        for l in reader:
            if not l[0].startswith('#'):
                line = Line(*l)
                if line.latex:
                    commands = [line.latex]
                else:
                    commands = []
                    
                if line.unimath:
                    commands.append(line.unimath)
                
                commands.extend(re.findall(tex, line.comment))
                
                item = (line.unicode, line.chr, line.cat)
                
                for command in commands:
                    if command not in symbols.keys():
                        symbols[command] = item
    for latex, item in latex_spaces:
        symbols[latex] = item
    
    return symbols
                

def _test():
    symbols = get_symbols()
    latex = [
        r'\overline',
        r'\underbar',
        r'\underline',
        r'\leftrightarrow',
        r'\leftarrow',
        r'\rightarrow',
        r'\overparen',
        r'\underparen',
        r'\overbrace',
        r'\underbrace',
        r'\quad',
        ]
    for l in latex:
        print(symbols[l])


if __name__ == '__main__':
    _test()