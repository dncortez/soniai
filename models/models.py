from pydantic import BaseModel
from typing import List, Optional, Tuple

class Plan(BaseModel):
    name: str
    schema: Schema
    parent: Optional[Plan]
    dependencies: List[Plan] = []
    allows: List[Plan] = []
    children: List[Plan] = []
    description: str = ""
    completed: bool = False
    shown_completed: bool = False
    position: Optional[Tuple[2]]
    is_open: bool = False

    def __post_init__(self):
        if self.parent is not None:
            self.parent.add_child(self.name)
        for child in self.children:
            child.set_parent(self)
        for dep in self.dependencies:
            dep.add_next(self)
        for next in self.allows:
            next.add_dependency(self)
        
    def is_doable(self):
        if self.parent is None or self.parent.is_doable():
            for dep in self.dependencies:
                if not (dep.completed or dep.shown_completed):
                    return False
        return True

    def is_root(self):
        return self.parent is None
    
    def is_base(self):
        return self.dependencies == []
    
    def is_vanguard(self):
        return self.allows == []
    
    def add_dependency(self, new: Plan):
        if new not in self.dependencies:
            self.dependencies.append(new)
            new.add_next(self)
    
    def add_next(self, new: Plan):
        if new not in self.allows:
            self.allows.append(new)
            new.add_dependency(self)
    
    def add_child(self, new: Plan):
        if new not in self.children:
            self.children.append(new)
            new.set_parent(self)

    def set_parent(self, new: Plan):
        if self.parent != new:
            self.parent = new
            new.add_child(self)
    
    def create_dependency(self, name: str):
        Plan(
            name=name,
            schema=self.schema,
            parent=self.parent,
            allows=[self]
        )
    
    def create_next(self, name: str):
        Plan(
            name=name,
            schema=self.schema,
            parent=self.parent,
            dependencies=[self]
        )

    def create_child(self, name: str):
        Plan(
            name=name,
            schema=self.schema,
            parent=self
        )


class Schema(Plan):
    pass