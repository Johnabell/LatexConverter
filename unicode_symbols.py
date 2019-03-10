import csv
import sys
import os
from collections import namedtuple
import re



symbol_file_name = 'unimathsymbols.txt'


def get_symbols():
    current_path = sys.path[0]
    file_path = os.path.join(current_path, symbol_file_name)
    Line = namedtuple('Line', ['unicode', 'chr', 'latex','unimath', 'cls','cat','req','comment'])
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
    return symbols
                

def _test():
    symbols = get_symbols()
    
    print(symbols[r'\mathbb{R}'])


if __name__ == '__main__':
    _test()