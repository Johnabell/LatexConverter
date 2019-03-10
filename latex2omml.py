"""
For converting latex to OMML. This file contains the a class for converting between latex
and OMML. It first converts the latex to mathML then using an XSLT file to transfrom the 
results. Initialise the class then use the convert method to return the OMML.


Author: John Bell
Email: bell.john.andrew@gmail.com
"""


import sys
import re
import logging
import traceback
import pprint

from lxml import etree
import Converter as l2m

mml2omml = 'MML2OMML2.xsl'
#logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(filename='latex.log',level=logging.DEBUG)
        
    
def ppmathml(mathml, type = 'string'):
    if type == 'string':
        mathml = etree.fromstring(mathml)
    elif type != 'xml':
        raise TypeError('Expected types string or xml')
    pp = etree.tostring(mathml, pretty_print=True, encoding='unicode')
    print(pp)
    return pp

class LatexConverter:
    def __init__(self): 
        xslt = etree.parse(mml2omml)
        self.transform = etree.XSLT(xslt)
        
    def convert(self, latex_input):
        logging.debug(latex_input)
        latex_input = self.handle_custom_commands(latex_input)
        logging.debug(latex_input)
        mathml_string = l2m.latex_to_mathml(latex_input, name_space = True)
        print(mathml_string)
        #mathml_string = etree.tostring(mathml_tree)
        logging.debug(mathml_string)
        mathml_tree = etree.fromstring(mathml_string)
        omml_tree = self.transform(mathml_tree)
        print(self.transform.error_log)
        return omml_tree.getroot()
        
 
        
    @staticmethod
    def handle_custom_commands(latex):
        nagwa_commands = {
            'nagwaMatrix': 'pmatrix',
            'nagwaCases' : 'cases'
            } 
        for nagwa_command, substitute in nagwa_commands.items():
            latex = latex.replace(nagwa_command, substitute)
        return latex


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
    converter = LatexConverter()
    summary = []
    for i, latex_input in enumerate(test_batch):
        print(('*' * 50) + '  Start of Test {} '.format(i+1) + ('*' * 50))
        print('Test for latex input: - "{}" \n'.format(latex_input))
        
        #print(converter._strip_align(latex_input))
        #x = etree.tostring(converter.convert(latex_input), pretty_print=True, encoding='unicode')
        #print(x)
        
        try:
            eqn = converter.convert(latex_input)
            x = etree.tostring(eqn, pretty_print=True, encoding='unicode')
            print(x)
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


    
if __name__ == '__main__':
    _test_mathml()