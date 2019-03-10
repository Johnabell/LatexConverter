"""
For converting latex to MathML. This file contains the main function for making the 
conversion (latex_to_mathml). It also contains a validator class (MathML_Validator) 
for checking the results.


Author: John Bell
Email: bell.john.andrew@gmail.com
"""


import sys
import os
import logging
import traceback

from lxml import etree

from MathObject import MathElement
from LatexParser import parse_latex, tokenizer


def latex_to_mathml(latex, name_space = True, to_string = True):
    math = etree.Element('math')
    if name_space:
        math.set('xmlns', "http://www.w3.org/1998/Math/MathML")
    root = parse_latex(latex)
    elem = root.to_mathml()
    math.append(elem)
    if to_string:
        return etree.tostring(math, pretty_print=True, encoding='unicode')
    else:
        return math
        
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
        current_path = os.path.dirname(os.path.realpath(__file__))
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
        

def _test_parser():
    test_batch = [
        r'\begin{align*}Q(t) = A\left(2^\frac{t}{B}\right)\end{align*}',
        r'\begin{align*} x+4 &= 5 \text{subtracting {4} from both sides} \\ x &= 1 \end{align*}',
        r'\binom{4}{4} = 1',
        r'f(x) = \left\{ \begin{array}{c} x^2 \text{ if } \; x > 0, \\ 0 \text{ if } x \leq 0 \end{array}\right.',
        r'x \in \mathbb{RC  \Gamma}',
        r"\begin{align*} \int_1^\infty \sin \left(\theta\right)dx = 5 \\ x = 4\end{align*}",
        r"""\begin{array}{c}
            a  b  c \\
            d  e  f \\
            g  h  i \end{array}""",
        r'$\underleftarrow{\lambda<0.28}.$',
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
        
        #print('MathML - Tokenizer output : ', [s for s in t.tokenize(latex_input)])
        
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


def _test_2():
    print(symbols[r'\quad'])
    
if __name__ == '__main__':
    #_test_2()
    _test_parser()