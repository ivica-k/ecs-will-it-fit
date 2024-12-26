from pydantic import BaseModel
from typing import Optional, Union
import re


class Attribute(BaseModel):
    name: str
    value: Optional[Union[str, None]] = None
    raw: Optional[Union[str, None]] = None

    def __hash__(self) -> int:
        return self.name.__hash__()

    def __gt__(self, other):
        return self.name > other.name

    def __lt__(self, other):
        return self.name < other.name

    def __str__(self) -> str:
        return self.raw or self.name

    def __eq__(self, other):
        return self.name == other.name and self.value == other.value

    def _parse_multiple(self):
        results = []
        name, value = re.match(
            r"attribute:(.+(?=\sin))\sin\s\[(.+(?=\]))", str(self)
        ).groups()

        values = value.replace("'", "").split(",")

        for value in values:
            results.append(Attribute(name=name, value=value.strip(), raw=str(self)))

        return results

    def _parse_dict(self):
        try:
            if "name" in self:
                name = self["name"]
                value = self.get("value", None)
                raw = self.get("name")

            elif "expression" in self:
                expression = self["expression"]
                raw = expression

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
                    pass

            else:
                pass

            return Attribute(
                name=name,
                value=value,
                raw=raw,
            )
        except UnboundLocalError as exc:
            a = 2

    @classmethod
    def parse_obj(cls, obj):
        return cls._parse_dict(obj)

    @classmethod
    def parse_multiple(cls, obj):
        return cls._parse_multiple(obj)
