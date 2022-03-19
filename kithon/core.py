import ast
from collections import defaultdict
from os import path, walk, listdir
import yaml
from hy.lex import hy_parse
from jinja2 import Template
from . import types, node as _node, transpiler_templates, __path__


def visitor(func):
    setattr(Transpiler, func.__name__, func)
    annotations = func.__annotations__['tree']
    if isinstance(annotations, tuple):
        for ann in annotations:
            Transpiler.elements[ann] = func
    else:
        Transpiler.elements[annotations] = func
    return func

class Transpiler:
    elements = {}

    def __init__(self):
        self.templates = transpiler_templates.default
        self.nl = 0
        self.namespace = '__main__'
        self.variables = {
            '__main__': {'type': types.types['module']('__main__')}
        }
        self.strings = []
        self.temp_var_counts = defaultdict(int)
        self.used = set([])

    def new_var(self, full_name, _type):
        if str(_type) in self.variables:
            self.variables.update({
                full_name + name.removeprefix(_type): var
                for name, var in self.variables.items()
                if name.startswith(_type)
            })
        self.variables.update({
            full_name: {
                'own': full_name,
                'type': _type,
                'immut': True
            }
        })

    def use(self, name):
        self.used.add(name)
        return ''

    def get_temp_var(self, base_name='temp'):
        """Get a unique temporary variable name."""
        self.temp_var_counts[base_name] += 1
        return f'{base_name}_{self.temp_var_counts[base_name]}'

    def previous_ns(self):
        if self.namespace == '__main__':
            return '__main__'
        return self.namespace[:self.namespace.rfind('.')]

    def node(self, tmp=None, parts=None, type=None, own=None):
        return _node.node(
            env=self, tmp=tmp,
            parts=parts, type=type,
            nl=self.nl, own=own
        )

    def get_lang(self, lang):
        translators_dirr = path.join(path.split(__path__[0])[0], 'translators')
        if lang not in listdir(translators_dirr):
            raise ValueError(f'{lang} is not supported')
        for dirr, _, files in walk(path.join(translators_dirr, lang)):
            for f in files:
                self.load_templs(
                    open(f'{dirr}/{f}', 'r', encoding='utf-8').read()
                )

    def load_templs(self, templates):
        templates = yaml.load(
            templates.expandtabs(2),
            Loader=yaml.FullLoader
        )
        if not templates:
            return
        for name, template in templates.items():
            self.add_templ(name, template)
    
    def add_templ(self, name, template):
        if name not in self.templates:
            self.templates[name] = {}
        if isinstance(template, str):
            self.templates[name].update({'tmp': Template(template)})
        elif isinstance(template, dict):
            for field, value in template.items():
                keywords = ['tmp', 'type', 'ignore_import', 'code', 'alt_name', 'ret_type']
                if field in keywords:
                    self.templates[name].update({field: value})
                else:
                    self.add_templ(f'{name}.{field}', value)

    def visit(self, tree, **kw):
        if type(tree) not in self.elements:
            return self.node()
        node = self.elements.get(type(tree))(
            self, tree,
            **(kw or {})
        )
        node.ast = tree
        return node

    def generate(self, code, lang='py', mode='main'):
        if lang == 'py':
            tree = ast.parse(code).body
        elif lang == 'hy':
            tree = hy_parse(code)[1:]
        elif lang == 'coco':
            from coconut.convenience import parse, setup
            setup(target='sys')
            tree = ast.parse(parse(code, 'block')).body
        for block in map(self.visit, tree):
            if not block:
                continue
            self.strings.extend(block.render().split('\n'))
        if mode == 'main':
            code = self.templates['main']['tmp'].render(
                _body=self.strings,
                body='\n'.join(self.strings),
                env=self
            )
            self.variables = {
                '__main__': {'type': types.types['module']('__main__')}
            }
            self.temp_var_counts = defaultdict(int)
        else:
            code = '\n'.join(self.strings)
        self.nl = 0
        self.namespace = '__main__'
        self.strings = []
        self.used = set([])
        return code
