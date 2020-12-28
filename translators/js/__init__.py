from . import blocks
from . import expr


a_func = {"print": "alert",
          "input": "prompt",
          "get_id": "document.getElementById",
}

a_attr = {"len":"length",
          "append":"push",
}

lib = {"math": {"__name__": "Math",
                "pi": "PI"
                },
       "json": {"__name__": "JSON",
                "dumps": "stringify",
                "loads": "parse"
                }
}

signs = {"+": "+",
         "-": "-",
         "*": "*",
         "/": "/",
         "**": "**",
         "//": lambda l, r: f"Math.floor({l}/{r})",
         "==": "===",
         "!=": "!==",
         ">": ">",
         "<": "<",
         ">=": ">=",
         "<=": "<=",
         "or": "||",
         "and": "&&",
         "|": "|",
         "&": "&",
         "%": "%",
         "not": "!"
}

expr_handlers = {"bin_op": expr.bin_op,
                 "bool_op": expr.bool_op,
                 "name": expr.name,
                 "un_op": expr.un_op,
                 "const": expr.const,
                 "string": expr.c_str,
                 "attr": expr.attr,
                 "call": expr.call,
                 "arg": expr.arg,
                 "index": expr.slice,
                 "compare": expr.compare,
                 "list": expr._list
}

blocks_handlers = {"assign": blocks.assign,
                   "new_var": blocks.new_var,
                   "expr": blocks.expr,
                   "aug_assign": blocks.aug_assign,
                   "if": blocks._if,
                   "statement_block": blocks.statement_block,
                   "else": blocks._else,
                   "else_if": blocks.else_if,
                   "def": blocks.def_f,
                   "return": blocks.ret,
                   "for": blocks._for,
                   "c_like_for": blocks.c_like_for,
                   "while": blocks._while
}
