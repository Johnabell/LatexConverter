"""
The class definitions for the MathObject tree nodes. Each node has a pass_token_tree method
for parsing the output of the latex parsers token tree. Once a token tree has been passed
you can use the to_mathml method to generate mathml fragments from any node. There is also
a pretty print function pprint to give a visual representation of the MathObject tree. 


Author: John Bell
Email: bell.john.andrew@gmail.com
"""

import re
import logging
import weakref
from collections import namedtuple
from functools import wraps
from itertools import groupby

from lxml import etree

import UnicodeSymbols as ucs

#logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(filename='latex.log',level=logging.DEBUG)
Token = namedtuple('Token', ['type', 'value'])

symbols = ucs.get_symbols()


class MathObject:
    pass


class MathElement:
    type_dict = {
        'mathpunct' : 'mo',
        'mathord' : 'mi',
        'mathopen' : 'mo', 
        'mathclose' : 'mo',
        'mathbin' : 'mo',
        'mathalpha' : 'mi',
        'mathrel' : 'mo',
        'mathfence' : 'mo',
        'mathaccent' : 'mo',
        'mathop' : 'mo',
        'mathradical' : 'mo',
        'mathover' : 'mover',
        'mathunder' : 'munder',
        'mathspace' : 'mtext'
    }
    
    def __init__(self, value = None, type = None, parent = MathObject):
        self.parent = weakref.ref(parent)
        self._elements = []
        self.value = value
        self.sub = None
        self.sup = None
        self.type = type
        self.group_name = 'group'
        self.default_group_class = MathElement
        self.default_element_class = MathElement
        
    def add_element(self, value = None, type = None, ME_type = None):
        if ME_type is None:
            ME_type = MathElement
        element = ME_type(value, type)
        element.parent = weakref.ref(self)
        self._elements.append(element)
        return element
        
    def add_sub(self, value = None, type = None, ME_type= None):
        if ME_type is None:
            ME_type = MathElement
        element = ME_type(value, type)
        element.parent = weakref.ref(self)
        self.sub = element
        return element
    
    def add_sup(self, value = None, type = None, ME_type = None):
        if ME_type is None:
            ME_type = MathElement
        element = ME_type(value, type)
        element.parent = weakref.ref(self)
        self.sup = element
        return element
    
    def pprint(self, indent = ''):
        print(indent, self.value)
        #print(indent, 'Type: {} -- Value: {}'.format(self.type, self.value))
        indent = indent + ' ' * 4
        # Print subscript
        if self.sub is not None:
            print(indent, self.sub.value)
            for element in self.sub._elements:
                element.pprint(indent + ' ' * 4)
        # Print superscript 
        if self.sup is not None:
            print(indent, self.sup.value)
            for element in self.sup._elements:
                element.pprint(indent + ' ' * 4) 
        # Print child elements
        for element in self._elements:
            element.pprint(indent)
            
    def parse_token_tree(self, token_tree):
        # If a single token is passed in embed in list
        if isinstance(token_tree, tuple):
            token_tree = [token_tree]
        i = 0 
        while i < len(token_tree):
            token = token_tree[i]
            if isinstance(token, tuple):
                #print(token, token.type)
                if token.type == 'WS':
                    i +=1
                    continue
                method = getattr(self, 'lp_' + token.type, None)
                if method is not None:
                    i = method(i, token, token_tree)
                else:
                    child = self.add_element(token.value, token.type, self.default_element_class)
            elif isinstance(token, list):
                child = self.add_element(self.group_name, self.group_name, self.default_group_class)
                child.parse_token_tree(token)
            else:
                raise TypeError('Unexpected type in token tree: {0} - {1!r}'.format(type(token), token))    
            i +=1
    
    def lp_MP(self, i, token, token_tree):
        child = self.add_element(token.value, token.type, ME_math_parentheses)
        return i
    
    def lp_COM(self, i, token, token_tree):
        child = self.add_element(token.value, token.type, ME_command)
        return i
        
    def lp_SYMB(self, i, token, token_tree):
        child = self.add_element(token.value, token.type, ME_symbol)
        return i
    
    def lp_NUM(self, i, token, token_tree):
        child = self.add_element(token.value, token.type, ME_num)
        return i
        
    def lp_BEG(self, i, token, token_tree):
        value = re.findall(r'\\begin\{([^}]*)\}', token.value)[0]
        child = self.add_element(value, token.type, ME_environment)
        i += 1
        
        # Check for alignment attributes - if found adds attributes to ME_environment class,
        # and passes the rest of the tree to the sub elements
        j=0
        first = token_tree[i][0]
        if isinstance(first, list):
            values = [t.value for t in first]
            if all(value in 'clr|' for value in values):
                child.alignment = values
                j=1
        sub_tree = token_tree[i][j:]
        child.parse_token_tree(self._split_by_line_and_align(sub_tree))
        return i+1
    
    def lp_MM_B_ALIGN(self, i, token, token_tree):
        child = self.add_element(token.value, token.type, ME_align)
        i += 1
        child.parse_token_tree(self._split_by_line_and_align(token_tree[i]))
        return i+1
    
    def lp_LEFT(self, i, token, token_tree):
        child = self.add_element('parentheses', 'LEFTRIGHT', ME_parentheses)
        i += 1
        paren = token_tree[i][0].value
        if paren.startswith('\\'):
            paren = paren[1:]
        elif paren == '.':
            paren = ''
        child.open = paren
        child.parse_token_tree(token_tree[i][1:])
        i += 2
        paren = token_tree[i].value
        if paren.startswith('\\'):
            paren = paren[1:]
        elif paren == '.':
            paren = ' '
        child.close = paren
        return i
        
    def lp_FRAC(self, i, token, token_tree):
        child = self.add_element('frac', token.type, ME_frac)
        num = child.add_num('num', MathElement)
        num.parse_token_tree(token_tree[i+1])
        den = child.add_den('den', MathElement)
        den.parse_token_tree(token_tree[i+2])        
        return i + 2
        
    def lp_BIN(self, i, token, token_tree):
        child = self.add_element('frac', token.type, ME_Binom)
        num = child.add_num('num', MathElement)
        num.parse_token_tree(token_tree[i+1])
        den = child.add_den('den', MathElement)
        den.parse_token_tree(token_tree[i+2])        
        return i + 2
        
    def lp_MATHFONT(self, i, token, token_tree):
        
        child = self.add_element(token.value, token.type, ME_mathfont)
        return i
        
    def lp_TEXT(self, i, token, token_tree):
        #text = re.findall(r'\\text\w*\{([^}]*)\}', token.value)[0]
        child = self.add_element(token.value, token.type, ME_text)
        i += 1
        child.parse_token_tree(token_tree[i])
        return i
        
    
    def lp_ROOT(self, i, token, token_tree):
        child = self.add_element(token.value, token.type, ME_root)
        child.index = re.findall(r'\\sqrt\[(.*)]', token.value)[0]
        i += 1
        ttree, i = self._check_ahead(token_tree, i)
        child.parse_token_tree(ttree)
        return i
    
    def lp_SQRT(self, i, token, token_tree):
        child = self.add_element(token.value, token.type, ME_root)
        i += 1
        ttree, i = self._check_ahead(token_tree, i)
        child.parse_token_tree(ttree)
        return i
        
    def _check_ahead(self, token_tree, i):
        if isinstance(token_tree[i], list):
            return token_tree[i], i
        else:
            if token_tree[i].type in ['FRAC', 'RIGHT', 'BIN']:
                return token_tree[i:i+3], i+2
            elif token_tree[i].type in ['SQRT', 'ROOT', 'TEXT', 'OVERUNDER', 'MATHFONT']:
                return token_tree[i:i+2], i+1
            else:    
                return token_tree[i], i
    
    def lp_SUB(self, i, token, token_tree):
        try:
            parent = self._elements[-1]
        except IndexError:
            parent = self.add_element('blank', MathElement)
        i += 1
        parent.add_sub('sub', MathElement)
        #print(i, token_tree[i])
        ttree, i = self._check_ahead(token_tree, i)
        parent.sub.parse_token_tree(ttree)
        
        try:
            next = token_tree[i+1]  
        except IndexError:
            next = None
       
        if next is not None:
            if not isinstance(next,list):
                if next.type == 'SUP':
                    i += 2
                    parent.add_sup('sup', MathElement)
                    parent.sup.parse_token_tree(token_tree[i])
        return i
            
    def lp_SUP(self, i, token, token_tree):
        try:
            parent = self._elements[-1]
        except IndexError:
            parent = self.add_element('blank', MathElement)
        i += 1
        parent.add_sup('sup', MathElement)
        #print(i, token_tree[i])
        ttree, i = self._check_ahead(token_tree, i)
        parent.sup.parse_token_tree(ttree)
        try:
            next = token_tree[i+1]  
        except IndexError:
            next = None
       
        if next is not None:
            if not isinstance(next,list):
                if next.type == 'SUB':
                    i += 2
                    parent.add_sub('sub', MathElement)
                    parent.sub.parse_token_tree(token_tree[i])
        return i
        
    def lp_OVERUNDER(self, i, token, token_tree):
        child = self.add_element(token.value, token.type, ME_overunder)
        i += 1
        child.parse_token_tree(token_tree[i])
        return i

  
    @staticmethod
    def _split_by_line_and_align(token_tree):
        NL =  Token(type='NL', value='\\\\')
        AMP = Token(type='AMP', value='&')
        
        # Regroups the tree into rows and elements
        tree_row_elem = [
            [list(elm) for not_AMP, elm in groupby(line, lambda x : x!= AMP) if not_AMP] 
            for not_NL, line in groupby(token_tree, lambda x: x != NL) if not_NL]  
        return tree_row_elem
        
    def _check_parent(func):
        """
        Decorator to add parent element if not pressent
        """
        @wraps(func)
        def wrapper(self, parent = None, *args, **kwrds):
            if parent is None:
                parent = etree.Element('math')
            result = func(self, parent, *args, **kwrds)
            return result
        return wrapper
    
    def _sub_sup_ml(func):
        """
        Decorator to add processing for super scripts and subscripts.
        """
        @wraps(func)
        def wrapper(self, parent = None, *args, **kwrds):
            scripts = self._sub_sup()
            if scripts is not None:
                parent = etree.SubElement(parent, scripts)
            result = func(self, parent, *args, **kwrds)
            
            for subsup in [s for s in [self.sub, self.sup] if s is not None]:
                if len(subsup._elements) > 1:
                    row = etree.SubElement(parent, 'mrow')
                else:
                    row = parent
                for el in subsup._elements:
                    el.to_mathml(row)
            return result
        return wrapper
        
    def _run_on_children(func):
        """
        Decorator to iterate the  processing onto the children
        """
        @wraps(func)
        def wrapper(self, *args, **kwrds):
            result = func(self, *args, **kwrds)
            
            for child in self._elements:
                child.to_mathml(result)
            return result
        return wrapper
        
    @_run_on_children
    @_check_parent
    @_sub_sup_ml
    def to_mathml(self, parent = None):
        scripts = self._sub_sup()
        
        element_name = 'mrow'
        elem = etree.SubElement(parent, element_name)
        #elem.text = self.value
        
        return elem
        
    def _sub_sup(self):
        if self.sup is not None and self.sub is not None:
            return 'msubsup'
        elif self.sup is not None:
            return 'msup'
        elif self.sub is not None:
            return 'msub'
        else:
            return None
    


class ME_mathfont(MathElement):
    @MathElement._check_parent
    @MathElement._sub_sup_ml
    def to_mathml(self, parent = None):
        elem = etree.SubElement(parent, 'mi')
        prefix, text = self.value[:-1].split('{')
        out = ''
        #print(prefix, t)
        for part in re.findall(r'\\\w*|\w', text):
            try:
                unicode, char, type = symbols[prefix + '{' + part + '}']
            except KeyError:
                char = part
            out += char
                
        elem.text = out
        return elem

class ME_text(MathElement):
    @MathElement._check_parent
    @MathElement._sub_sup_ml
    def to_mathml(self, parent = None):
        elem = etree.SubElement(parent, 'mtext')
        
        elem.text = self.value
        return elem
        
    def parse_token_tree(self, token_tree, string = ''):
        # If a single token is passed in embed in list
        if isinstance(token_tree, tuple):
            token_tree = [token_tree]
        i = 0 
        while i < len(token_tree):
            token = token_tree[i]
            if isinstance(token, tuple):
                #print(token, token.type)
                string += token.value
            elif isinstance(token, list):
                string = self.parse_token_tree(token, string)
            else:
                raise TypeError('Unexpected type in token tree: {0} - {1!r}'.format(type(token), token))    
            i +=1
        self.value = string
        return string    
    

class ME_math_parentheses(MathElement):
    @MathElement._run_on_children
    @MathElement._check_parent
    @MathElement._sub_sup_ml
    def to_mathml(self, parent):
        try:
            unicode, char, type = symbols[self.value]
            cat = self.type_dict[type]
        except KeyError:
            char = self.value[1:]
            cat = 'mo'
            
        elem = etree.SubElement(parent, cat)
        elem.set('fence', 'true')
        elem.text = char
        return elem

class ME_command(MathElement):
    @MathElement._check_parent
    @MathElement._sub_sup_ml
    def to_mathml(self, parent = None):
        try:
            unicode, char, type = symbols[self.value]
            cat = self.type_dict[type]
        except KeyError:
            char = self.value[1:]
            cat = 'mi'
            
        elem = etree.SubElement(parent, cat)
        elem.text = char
        return elem
        
class ME_symbol(MathElement):
    @MathElement._check_parent
    @MathElement._sub_sup_ml
    def to_mathml(self, parent = None):
        try:
            unicode, char, type = symbols[self.value]
            cat = self.type_dict[type]
        except KeyError:
            char = self.value[1:]
            cat = 'mo'
            
        elem = etree.SubElement(parent, cat)
        elem.text = char
        return elem
 
        
class ME_parentheses(MathElement):
    def __init__(self, *args, **kwrds):
        super().__init__(*args, **kwrds)
        self.open = None
        self.close = None
    
    @MathElement._run_on_children
    @MathElement._check_parent
    @MathElement._sub_sup_ml
    def to_mathml(self, parent):
        elem = etree.SubElement(parent, 'mfenced')
        elem.set('open', self.open)
        elem.set('close', self.close)
        elem.set('separators', '')
        row = etree.SubElement(elem, 'mrow')
        return row

class ME_element(MathElement):
    @MathElement._run_on_children
    @MathElement._check_parent
    def to_mathml(self, parent):
        #print(self.parent().parent().alignment)
        elem = etree.SubElement(parent, 'mtd')
        
        return elem

class ME_row(MathElement):
    def __init__(self, *args, **kwrds):
        super().__init__(*args, **kwrds)
        self.group_name = 'element'
        self.default_group_class = ME_element   

    @MathElement._run_on_children
    @MathElement._check_parent
    def to_mathml(self, parent):
        elem = etree.SubElement(parent, 'mtr')
        return elem
        
class ME_line(MathElement):
    def __init__(self, *args, **kwrds):
        super().__init__(*args, **kwrds)
        self.group_name = 'alignment_blocks'    
        self.default_group_class = ME_alignment_blocks
    
    @MathElement._run_on_children
    @MathElement._check_parent
    def to_mathml(self, parent):
        elem = etree.SubElement(parent, 'mtr')
        return elem
    
    
class ME_alignment_blocks(MathElement):
    @MathElement._run_on_children
    @MathElement._check_parent
    def to_mathml(self, parent):
        elem = etree.SubElement(parent, 'mtd')
        row = etree.SubElement(elem, 'mrow')
        align = etree.SubElement(row, 'maligngroup')
        return row

class ME_frac(MathElement):
    def __init__(self, *args, **kwrds):
        super().__init__(*args, **kwrds)
        self.num = None
        self.den = None
        
          
    def add_num(self, value = None, type = None, ME_type = None):
        if ME_type is None:
            ME_type = MathElement
        num = ME_type(value)
        num.parent = weakref.ref(self)
        self.num = num
        return num
        
    def add_den(self, value = None, type = None, ME_type = None):
        if ME_type is None:
            ME_type = MathElement
        den = ME_type(value)
        den.parent = weakref.ref(self)
        self.den = den
        return den
        
    def pprint(self, indent = 0):
        print(indent, self.value)
        indent = indent + ' ' * 4
        self.num.pprint(indent)
        self.den.pprint(indent)
        
    @MathElement._check_parent
    def to_mathml(self, parent= None):
        elem = etree.SubElement(parent, 'mfrac')
        for numden in [s for s in [self.num, self.den] if s is not None]:
            if len(numden._elements) > 1:
                row = etree.SubElement(elem, 'mrow')
            else:
                row = elem
            for el in numden._elements:
                el.to_mathml(row)
        return elem
        
class ME_Binom(ME_frac):
    def to_mathml(self, parent = None):
        elem = super().to_mathml(parent)
        elem.set('linethickness', '0')
        return elem

 
class ME_environment(MathElement):
    matrix_paren = {
        'pmatrix' : ('(', ')'),
        'bmatrix' : ('[', ']'),
        'Bmatrix' : ('{', '}'),
        'vmatrix' : ('|', '|'),
        'Vmatrix' : ('‖', '‖'),
        'cases' : ('{', '')
        }
        
    _alignment_dict = {
        'c' : 'center',
        'r' : 'right',
        'l' : 'left'
        }
    
    def __init__(self, *args, **kwrds):
        super().__init__(*args, **kwrds)
        self.rows = [[]]
        self.group_name = 'row'
        self.default_group_class = ME_row
        self.alignment = None
        self._row_number = 0
    
    def _handle_alignment(self, elem):
        if self.alignment is not None:
            lines = ['solid' for e in self.alignment if e == '|']
            alignments = [self._alignment_dict[e] for e in self.alignment if e != '|']
            if lines:
                if len(lines) >= len(alignments):
                    elem.set('frame', 'solid')
                elif len(lines) < len(alignments) - 1:
                    lines.append('none')
                elem.set('columnlines', ' '.join(lines))
            
            if alignments:
                elem.set('columnalign', ' '.join(alignments))
        
        
    
    #@_handle_paren
    @MathElement._run_on_children
    @MathElement._check_parent    
    def to_mathml(self, parent):
        if self.value in self.matrix_paren.keys():
            paren = self.matrix_paren[self.value]
            parent = etree.SubElement(parent, 'mfenced')
            parent.set('open', paren[0])
            parent.set('close', paren[1])
            parent.set('separators', '')
            
        
        elem = etree.SubElement(parent, 'mtable')
        self._handle_alignment(elem)
        
        #alignement handeling
        
        return elem
        
        
    
        
    
    
class ME_align(ME_environment):
    def __init__(self, *args, **kwrds):
        super().__init__(*args, **kwrds)
        self.group_name = 'line'
        self.default_group_class = ME_line

    @MathElement._run_on_children
    @MathElement._check_parent    
    def to_mathml(self, parent):
        elem = etree.SubElement(parent, 'mtable')
        elem.set('columnalign', 'right left' )
        return elem
        
class ME_root(MathElement):
    def __init__(self, *args, **kwrds):
        super().__init__(*args, **kwrds)
        self.index = None
    
    @MathElement._run_on_children    
    @MathElement._check_parent
    def to_mathml(self, parent = None):
        if self.index is None:
            elem = etree.SubElement(parent, 'msqrt')
        else:
            elem = etree.SubElement(parent, 'mroot')
            row1 = etree.SubElement(elem, 'mrow')
            index = etree.SubElement(row1, 'mn')
            index.text = self.index
        row = etree.SubElement(elem, 'mrow')
        for child in self._elements:
            child.to_mathml(row)
            
class ME_overunder(MathElement):
    _sym_dict = {
        '00305' : '_',
        '00331' : '-',
        '00332' : '_',
        '020E1' : '↔',
        '020EE' : '←', 
        '020EF' : '→', 
        '023DC' : '⏜',
        '023DD' : '⏝',
        '023DE' : '⏞',
        '023DF' : '⏟'
        }
    
    @MathElement._check_parent
    @MathElement._sub_sup_ml
    def to_mathml(self, parent = None):
        if self.value.startswith(r'\over'):
            elem = etree.SubElement(parent, 'mover')
        else: 
            elem = etree.SubElement(parent, 'munder')
        row = etree.SubElement(elem, 'mrow')
        for child in self._elements:
            child.to_mathml(row)
        accent = etree.SubElement(elem, 'mo')
        unicode, char, type = symbols[self.value]
        accent.text = self._sym_dict[unicode]
        return elem           
 
class ME_num(MathElement):
    @MathElement._check_parent
    @MathElement._sub_sup_ml
    def to_mathml(self, parent = None):
        elem = etree.SubElement(parent, 'mn')
        elem.text = self.value
        return elem
        
    def pprint(self, indent):
        super().pprint(indent)
        #print(etree.tostring(self.to_mathml(), pretty_print=True, encoding='unicode'))
 