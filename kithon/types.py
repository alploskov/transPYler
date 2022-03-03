from dataclasses import make_dataclass
from jinja2 import Template
from jinja2.nativetypes import NativeTemplate


def to_any(__type):
    return getattr(__type, 'to_any', lambda: 'any')()

def dict_to_any(self):
    if self.key_type == self.el_type == 'any':
        return 'any'
    if self.el_type == 'any':
        return types['dict'](to_any(self.key_type), 'any')
    if self.key_type == 'any':
        return types['dict']('any', to_any(self.el_type))
    return types['dict'](self.key_type, to_any(self.el_type))

def type_simplification(_type):
    yield _type
    while _type != 'any':
        _type = to_any(_type)
        yield _type

def _type(name, fields, tmp='', to_any=(lambda self: 'any')):
    _type = make_dataclass(name, fields)
    _type.render = (lambda self:
        Template(tmp or name).render(**self.__dict__)
    )
    _type.__str__ = lambda self: self.render()
    _type.to_any = to_any
    types.update({name: _type})
    return _type

types = {}
_type(
    'list',
    fields=['el_type'],
    tmp='list[{{el_type}}]',
    to_any=(
        lambda s: 'any' if s.el_type == 'any'
        else types['list'](to_any(s.el_type))
    )
)
_type(
    'dict',
    fields=['key_type', 'el_type'],
    tmp='dict[{{key_type}}]{{el_type}}',
    to_any=dict_to_any
)
_type(
    'tuple',
    fields=['el_type', 'els_types'],
    tmp='tuple[{{els_types|join(", ")}}]'
)
_type(
    'func',
    fields=['name', 'args', 'ret_type'],
    tmp='func[{{args|join(", ")}}]'
)
_type('module', fields=['name'], tmp='mode_{{name}}')

def type_eval(type_code, parts=None):
    """
    Generate type from macros
    """
    if not type_code:
        return None
    executor = lambda x: type_eval(x, parts=parts)
    if isinstance(type_code, list):
        _types = tuple(map(executor, type_code))
        return types['tuple'](tuple(set(_types)), _types)
    if (isinstance(type_code, dict)
        and (base_type := list(type_code.keys())[0]) in types
    ):
        return types[base_type](*map(
            executor,
            list(*type_code.values())
        ))
    return NativeTemplate(type_code).render(**parts)

# creating new types in config
# matrix:
#   attrs:
#     el_type: generic
#   tmp:
#     matrix[{{el_type}}]
#
