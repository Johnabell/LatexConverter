"""
Parses the Latex Expression and create a MathObject: a tree of connected nodes representing
the mathematical expression.


Author: John Bell
Email: bell.john.andrew@gmail.com
"""

import os
import re
import logging
import traceback
import weakref
from collections import namedtuple
from functools import wraps
import pprint
from itertools import groupby
from lxml import etree

from MathObject import MathElement


#logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(filename='latex.log',level=logging.DEBUG)
Token = namedtuple('Token', ['type', 'value'])

def parse_latex(latex):
    ignore_tags = ['MM_DMATH', 'MM_BILMATH', 'MM_EINMATH']
    tokens = tokenizer(latex, ignore_tags)
    root = MathElement()
    token_tree = _group(tokens)
    pprint.pprint(token_tree)
    #math_object = build_math_object(token_tree, MathElement())
    root.parse_token_tree(token_tree)
    #root.pprint()
    print(etree.tostring(root.to_mathml(), pretty_print=True, encoding='unicode'))
    #print('ran_sucessfully')
    return root
    
def tokenizer(latex, ignore_types = ['WS']):
    _patterns = [
        r'(?P<NUM>[0-9]+\.?[0-9]*)',
        r'(?P<MM_B_ALIGN>\\begin\{align\*?\})',
        r'(?P<MM_E_ALIGN>\\end\{align\*?\})',
        r'(?P<MM_DMATH>\\\[|\$\$|\\\])',
        r'(?P<MM_BILMATH>^\$)',
        r'(?P<MM_EINMATH>\$$)',
        r'(?P<BEG>\\begin\{[^}]*\})',
        r'(?P<END>\\end\{[^}]*\})',
        r'(?P<NL>\\\\)',
        r'(?P<MP>\\[{}|])',
        r'(?P<TEXT>\\text\w*)',
        r'(?P<MATHFONT>\\math\w*\{[^}]*})',
        r'(?P<GB>\{)',
        r'(?P<GE>\})',
        r'(?P<ROOT>\\sqrt\[([^]]*)\])',
        r'(?P<SQRT>\\sqrt)',
        r'(?P<SUB>\_)',
        r'(?P<SUP>\^)',
        r'(?P<LEFT>\\left(?!\w))',
        r'(?P<RIGHT>\\right(?!\w))',
        r'(?P<FRAC>\\frac)',
        r'(?P<BIN>\\binom)',
        r'(?P<OVERUNDER>\\over[a-z]*|\\under[a-z]*)',
        r'(?P<COM>\\[A-Za-z]+|\\[,:;\s])',
        r'(?P<WS>\s+)',
        r'(?P<AMP>&)',
        r'(?P<SYMB>.)'
        ]
    patterns = re.compile('|'.join(_patterns))
    sn = patterns.scanner(latex)
    Token = namedtuple('Token', ['type', 'value'])
    for m in iter(sn.match, None):
        token = Token(m.lastgroup,m.group())
        if m.lastgroup not in ignore_types:
            yield token

    
def _group(tokens):
    begin_group_tokens = ['GB', 'BEG', 'LEFT', 'MM_B_ALIGN']
    end_group_tokens = ['GE', 'END', 'RIGHT', 'MM_E_ALIGN']
        
    l_tokens = [t for t in tokens]
    #print(l_tokens)
    tokens = iter(l_tokens)
    group = []
    stack = []
    tree = []
    for i, token in enumerate(tokens):
        if token.type in begin_group_tokens:
            if len(stack) == 0:
                if token.type != 'GB':
                    group.append(token)
                if group:
                    #print('Group : ', group)
                    tree.extend(group)
                    group = []
            else:
                group.append(token)
            stack.append(token)
            
            
        elif token.type in end_group_tokens:
            stack.pop()
            group.append(token)
            if group and len(stack) == 0: 
                #print('Group : ', group)
                tree.append(_group(iter(group[:-1])))
                group = []
                if token.type != 'GE':
                    group.append(token)
    
        else:
            group.append(token)
    if group:
        tree.extend(group)
    return tree
        
    
