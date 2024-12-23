from pydantic import BaseModel
from typing import Optional, Union
import re


class Attribute(BaseModel):
    name: str
    value: Optional[Union[str, None]] = None

    def __hash__(self) -> int:
        return self.name.__hash__()

    def __gt__(self, other):
        return self.name > other.name

    def __lt__(self, other):
        return self.name < other.name

    def __eq__(self, other):
        try:
            return self.name == other.name and self.value == other.value
        except AttributeError:
            a = 2

    def _parse_dict(self):
        try:
            if "name" in self:
                name = self["name"]
                value = self.get("value", None)
            elif "expression" in self:
                expression = self["expression"]

                if "==" in expression:
                    _, value = expression.split("==")
                    name = _.replace("attribute:", "")

                elif "[" in expression and "]" in expression:
                    name, value = re.match(
                        r"attribute:(.+(?=\sin))\sin\s\[(.+(?=\]))", expression
                    ).groups()

                elif "exists" in expression:
                    name = re.match(r"attribute:(.+(?=\s))", expression).groups()[0]

                    value = None

                else:
                    a = 2

            else:
                a = 3

            return Attribute(
                name=name,
                value=value,
            )
        except UnboundLocalError as exc:
            a = 2

    @classmethod
    def parse_obj(cls, obj):
        return cls._parse_dict(obj)
