from enum import Enum


class ARType(Enum):         # Activation Record Type
    PROGRAM = 'PROGRAM'
    MAIN    = 'MAIN'
    TASK    = 'TASK'
    BEHAVIOR= 'BEHAVIOR'
    ACTION  = 'ACTION'
    AGENT   = 'AGENT'
    RPC     = 'RPC'


class ActivationRecord:
    def __init__(self, name, category, nesting_level):
        self.name = name
        self.category = category
        self.nesting_level = nesting_level
        self.members = {}

    def __setitem__(self, key, value):
        self.members[key] = value

    def __getitem__(self, key):
        return self.members[key]

    def get(self, key):
        return self.members.get(key)

    def __str__(self):
        lines = [
            '{level}: {category} {name}'.format(
                level=self.nesting_level,
                category=self.category.value,
                name=self.name,
            )
        ]
        for name, val in self.members.items():
            lines.append(f'   {name:<20}: {val}')

        s = '\n'.join(lines)
        return s

    def __repr__(self):
        return self.__str__()


class CallStack:
    def __init__(self):
        self._records = []

    def push(self, ar):
        self._records.append(ar)

    def pop(self):
        return self._records.pop()

    def peek(self):
        return self._records[-1]
    
    def bottom(self):
        return self._records[0]

    def __str__(self):
        minus = '-' * 30
        equal = '=' * 30
        s = '\n'.join(repr(ar) for ar in reversed(self._records))
        s = f'{equal}\nCALL STACK\n{minus}\n{s}\n{equal}\n\n'
        return s

    def __repr__(self):
        return self.__str__()

