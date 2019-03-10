import sys
sys.path.append("/Users/johnbell/Dropbox (Nagwa)/Python/latex2omml/latex2mathml/")

#import converter as l2ml
import os
import tokenizer as t
import symbols_parser as sp
import unicode_symbols as ucs
#import aggregator as ag
from lxml import etree
import re
import logging
import traceback
import sys
import weakref
from collections import namedtuple
from functools import wraps
from inspect import signature
import pprint
from itertools import tee
from itertools import groupby


mml2omml = 'MML2OMML2.xsl'
#logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(filename='latex.log',level=logging.DEBUG)
Token = namedtuple('Token', ['type', 'value'])

symbols2 = sp.parse_symbols()
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
        'mathunder' : 'munder'
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
            paren = ' '
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
        
    def lp_MATHFONT(self, i, token, token_tree):
        
        child = self.add_element(token.value, token.type, ME_mathfont)
        return i
        
    def lp_TEXT(self, i, token, token_tree):
        text = re.findall(r'\\text\w*\{([^}]*)\}', token.value)[0]
        child = self.add_element(text, token.type, ME_text)
        return i
        
    
    def lp_ROOT(self, i, token, token_tree):
        child = self.add_element(token.value, token.type, ME_root)
        child.index = re.findall(r'\\sqrt\[(.*)]', token.value)[0]
        i += 1
        child.parse_token_tree(token_tree[i])
        return i
    
    def lp_SQRT(self, i, token, token_tree):
        child = self.add_element(token.value, token.type, ME_root)
        i += 1
        child.parse_token_tree(token_tree[i])
        return i
        
    def lp_SUB(self, i, token, token_tree):
        try:
            parent = self._elements[-1]
        except IndexError:
            parent = self.add_element('blank', MathElement)
        i += 1
        parent.add_sub('sub', MathElement)
        #print(i, token_tree[i])
        parent.sub.parse_token_tree(token_tree[i])
        try:
            next = token_tree[i+1]  
        except IndexError:
            next = None
       
        if next is not None:
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
        parent.sup.parse_token_tree(token_tree[i])
        try:
            next = token_tree[i+1]  
        except IndexError:
            next = None
       
        if next is not None:
            if next.type == 'SUB':
                i += 2
                parent.add_sub('sub', MathElement)
                parent.sub.parse_token_tree(token_tree[i])
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
    
class ME_environment(MathElement):
    matrix_paren = {
        'pmatrix' : ('(', ')'),
        'bmatrix' : ('[', ']'),
        'Bmatrix' : ('{', '}'),
        'vmatrix' : ('|', '|'),
        'Vmatrix' : ('‖', '‖'),
        }
    
    def __init__(self, *args, **kwrds):
        super().__init__(*args, **kwrds)
        self.rows = [[]]
        self.group_name = 'row'
        self.default_group_class = ME_row
    
    def _handle_paren(func):
        """
        Decorator to add parentheses to the matrix
        """
        @wraps(func)
        def wrapper(self, parent, *args, **kwrds):
            if self.value in self.matrix_paren.keys():
                paren = self.matrix_paren[self.value]
                open = etree.SubElement(parent, 'mo')
                open.text = paren[0]
                result = func(self, parent, *args, **kwrds)
                close = etree.SubElement(parent, 'mo')
                close.text = paren[1]
            else: 
                result = func(self, *args, **kwrds)
            return result
        return wrapper
    
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
            r'(?P<TEXT>\\text\w*\{[^}]*\})',
            r'(?P<MATHFONT>\\math\w*\{[^}]*})',
            r'(?P<GB>\{)',
            r'(?P<GE>\})',
            r'(?P<ROOT>\\sqrt\[([^]]*)\])',
            r'(?P<SQRT>\\sqrt)',
            r'(?P<SUB>\_)',
            r'(?P<SUP>\^)',
            r'(?P<LEFT>\\left)',
            r'(?P<RIGHT>\\right)',
            r'(?P<FRAC>\\frac)',
            r'(?P<COM>\\[A-Za-z]*)',
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
                

def parse_latex(latex):
    ignore_tags = ['WS', 'MM_DMATH', 'MM_BILMATH', 'MM_EINMATH']
    tokens = tokenizer(latex, ignore_tags)
    root = MathElement()
    token_tree = _group(tokens)
    #pprint.pprint(token_tree)
    #math_object = build_math_object(token_tree, MathElement())
    root.parse_token_tree(token_tree)
    #root.pprint()
    print(etree.tostring(root.to_mathml(), pretty_print=True, encoding='unicode'))
    #print('ran_sucessfully')
    return root
    
def latex_to_mathml(latex, name_space = True):
    math = etree.Element('math')
    if name_space:
        math.set('xmlns', "http://www.w3.org/1998/Math/MathML")
    root = parse_latex(latex)
    elem = root.to_mathml()
    math.append(elem)
    return math
    
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
        
    
def ppmathml(mathml, type = 'string'):
    if type == 'string':
        mathml = etree.fromstring(mathml)
    elif type != 'xml':
        raise TypeError('Expected types string or xml')
    pp = etree.tostring(mathml, pretty_print=True, encoding='unicode')
    print(pp)
    return pp


class MathML_Validator:
    schema_path = 'mathml2'
    schema_file = 'mathml2.dtd'
    
    def __init__(self):
        current_path = sys.path[0]
        DTD_location = os.path.join(current_path, self.schema_path, self.schema_file)
        self.DTD = etree.DTD(DTD_location)
        
    def validate_from_etree(self, tree):
        result = self.DTD.validate(tree)
        log = self.DTD.error_log
        error = log.last_error
        self.DTD._clear_error_log()
        return result, log.last_error
    
    def validate_from_string(self, string):
        tree = etree.fromstring(mathml)
        self.validate_from_etree(tree)
        

def validator(mathml):
    schema_path = 'mathml2'
    schema_file = 'mathml2.dtd'
    current_path = sys.path[0]
    schema_location = os.path.join(current_path, schema_path, schema_file)
    DTD = etree.DTD(schema_location)
    #xmlschema = etree.XMLSchema(xmlschema_doc)
#     
    mathml = """
        
        <mrow>
  <mtable>
    <mtd>
      <mtr>
        <mrow>
          <maligngroup/>
          <msubsup>
            <mi>∫</mi>
            <mn>1</mn>
            <mi>∞</mi>
          </msubsup>
          <mi>sin!!!!!!!!</mi>
          <mfenced open="(" close=")" seperator="">
            <mrow>
              <mi>θ</mi>
            </mrow>
          </mfenced>
          <mi>d</mi>
          <mi>x</mi>
          <mi>=</mi>
          <mn>5</mn>
        </mrow>
      </mtr>
    </mtd>
    <mtd>
      <mtr>
        <mrow>
          <maligngroup/>
          <mi>x</mi>
          <mi>=</mi>
          <mn>4</mn>
        </mrow>
      </mtr>
    </mtd>
  </mtable>
</mrow>

"""
    #parser = etree.XMLParser(dtd_validation=True)
    
    doc2 = etree.fromstring(mathml)
    result = DTD.validate(doc2)
    log = DTD.error_log
    return result, log.last_error
    

def _test_parser():
    test_batch = [
        r'f(x) = \left\{ \begin{array}{c} x^2 \text{ if }  x > 0, \\ 0 \text{ if } x \leq 0 \end{array}\right.',
        r'x \in \mathbb{RC  \Gamma}',
        r"\begin{align*} \int_1^\infty \sin \left(\theta\right)dx = 5 \\ x = 4\end{align*}",
        r"""\begin{array}{c}
            a  b  c \\
            d  e  f \\
            g  h  i \end{array}""",
        r'$\lambda<0.28.$',
        r'$$\{1,2,3\}$$',
        r"""\begin{align*} \vert 1.4-1.2\vert &=0.2,\\ \vert 1.4-1.4\vert &=0,\\ \vert 1.4-0.9
        \vert &=0.5,\\ \vert 1.4-1.8\vert &=0.4,\\ \vert 1.4-1.7\vert &=0.3. \end{align*}""",
        r'$3x\left[x+\left(y-x\right)\right]+y\left[2y+2\left(x-y\right)\right]$',
        r"""\begin{align*} \frac{1}{\det{(A)}}A^* =\begin{nagwaMatrix}\frac{d}{\det{(A)}}&
        \frac{b}{\det{(A)}}\\ -\frac{c}{\det{(A)}}&\frac{a}{\det{(A)}}\end{nagwaMatrix} 
        \end{align*}""",
        r'$^*$',
        r'$1\left[5^3=1 \cdot 5 \cdot 5 \cdot 5\right]$',
        r'$M=\begin{pmatrix}m_{ij}\end{pmatrix}$',
        r"""\begin{align*} \frac{1}{\det{(A)}}A^* =\begin{nagwaMatrix}\frac{d}{\det{(A)}}&
        \frac{b}{\det{(A)}}\\ -{3}\end{nagwaMatrix} 
        \end{align*}""",
        r"""\begin{bmatrix}
             a_{1,1} & a_{1,2} & \cdots & a_{1,n} \\
             a_{2,1} & a_{2,2} & \cdots & a_{2,n} \\
             \vdots  & \vdots  & \ddots & \vdots  \\
             a_{m,1} & a_{m,2} & \cdots & a_{m,n} 
            \end{bmatrix}""",
        r'\begin{matrix} 1 & -\sqrt[3]{2} \end{matrix}'
    ]
    check = MathML_Validator()
    summary = []
    for i, latex_input in enumerate(test_batch):
        print(('*' * 50) + '  Start of Test {} '.format(i+1) + ('*' * 50))
        print('Test for latex input: - "{}" \n'.format(latex_input))
        
        print('MathML - Tokenizer output : ', [s for s in t.tokenize(latex_input)])
        
        try:
            print('Tokenizer output : ', [t for t in tokenizer(latex_input)])
            print('Parser output: ')
            mathobject = parse_latex(latex_input)
            valid, log = check.validate_from_etree(mathobject.to_mathml())
            print('Validator result', valid, log,)
            print(('+' * 50) + '  Test Success  ' + ('+' * 50))
            summary.append('{} - Success for latex input -  "{}" \n\t Valid mathml: - {} \t Error log : - {}'.format(i+1, latex_input, valid, log))
        except Exception as e:
            exc_info = sys.exc_info()
            print(('-' * 50) + '  Test Failure  ' + ('-' * 50))
            print(e)
            traceback.print_exception(*exc_info, file=sys.stdout)
            del exc_info
            summary.append('{} - Falure for latex input - "{}"'.format(i+1, latex_input))
        finally:
            print(('*' * 50) + '  End of Test {} '.format(i+1) + ('*' * 50) + ('\n' * 5))
    
    print('\n'.join(summary))

def _test_mathml():
    test_batch = [
        r"\begin{align*} \int_1^\infty \sin \left(\theta\right)dx = 5 \\ x = 4\end{align*}",
        r"""\begin{array}{c}
            a  b  c \\
            d  e  f \\
            g  h  i \end{array}""",
        r'$\lambda<0.28.$',
        r'$$\{1,2,3\}$$',
        r"""\begin{align*} \vert 1.4-1.2\vert &=0.2,\\ \vert 1.4-1.4\vert &=0,\\ \vert 1.4-0.9
        \vert &=0.5,\\ \vert 1.4-1.8\vert &=0.4,\\ \vert 1.4-1.7\vert &=0.3. \end{align*}""",
        r'$3x\left[x+\left(y-x\right)\right]+y\left[2y+2\left(x-y\right)\right]$',
        r"""\begin{align*} \frac{1}{\det{(A)}}A^* =\begin{nagwaMatrix}\frac{d}{\det{(A)}}&
        \frac{b}{\det{(A)}}\\ -\frac{c}{\det{(A)}}&\frac{a}{\det{(A)}}\end{nagwaMatrix} 
        \end{align*}""",
        r'$^*$',
        r'$1\left[5^3=1 \cdot 5 \cdot 5 \cdot 5\right]$',
        r'$M=\begin{pmatrix}m_{ij}\end{pmatrix}$',
        r"""\begin{align*} \frac{1}{\det{(A)}}A^* =\begin{nagwaMatrix}\frac{d}{\det{(A)}}&
        \frac{b}{\det{(A)}}\\ -{3}\end{nagwaMatrix} 
        \end{align*}""",
        r"""\begin{bmatrix}
             a_{1,1} & a_{1,2} & \cdots & a_{1,n} \\
             a_{2,1} & a_{2,2} & \cdots & a_{2,n} \\
             \vdots  & \vdots  & \ddots & \vdots  \\
             a_{m,1} & a_{m,2} & \cdots & a_{m,n} 
            \end{bmatrix}""",
        r'\begin{matrix} 1 & -\sqrt{2} \end{matrix}'
    ]
    summary = []
    for i, latex_input in enumerate(test_batch):
        print(('*' * 50) + '  Start of Test {} '.format(i+1) + ('*' * 50))
        print('Test for latex input: - "{}" \n'.format(latex_input))
        print('Tokenizer output : ', [s for s in t.tokenize(latex_input)])
        print('Aggregator output: ', ag.aggregate(latex_input))
        
        #print(converter._strip_align(latex_input))
        #x = etree.tostring(converter.convert(latex_input), pretty_print=True, encoding='unicode')
        #print(x)
        
        try:
            ppmathml(l2ml.convert(latex_input))
            print(('+' * 50) + '  Test Success  ' + ('+' * 50))
            summary.append('{} - Success for latex input -  "{}"'.format(i+1, latex_input))
        except Exception as e:
            exc_info = sys.exc_info()
            print(('-' * 50) + '  Test Failure  ' + ('-' * 50))
            print(e)
            traceback.print_exception(*exc_info, file=sys.stdout)
            del exc_info
            summary.append('{} - Falure for latex input - "{}"'.format(i+1, latex_input))
        finally:
            print(('*' * 50) + '  End of Test {} '.format(i+1) + ('*' * 50) + ('\n' * 5))
    
    print('\n'.join(summary))
#     mathml_string = l2ml.convert(latex_input)
#     mathml_string = mathml_string[:5] + ' xmlns="http://www.w3.org/1998/Math/MathML"' + mathml_string[5:]
#     mathml_tree = etree.fromstring(mathml_string)
#     
#     print(etree.tostring(mathml_tree, pretty_print=True, encoding='unicode'))
#     xslt = etree.parse(mml2omml)
#     transform = etree.XSLT(xslt)
#     omml_tree = transform(mathml_tree)
#     print(etree.tostring(omml_tree.getroot(), pretty_print=True, encoding='unicode'))

def _test_2():
    print(symbols[r'\quad'])
    
if __name__ == '__main__':
    #_test_2()
    #_test_mathml()
    _test_parser()