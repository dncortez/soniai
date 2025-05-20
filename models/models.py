import json
from hashlib import sha1
from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Tuple, Dict



class BaseTask(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    name: str

class Plan(BaseTask):
    root: BaseTask = None

    def model_post_init(self, __context):
        self.root = Task(
            level=0,
            name=self.name,
            plan=self
        )

class Task(BaseTask):
    id: int = None
    plan: Plan
    level: int
    parent: Optional[BaseTask] = None
    dependencies: List[BaseTask] = []
    nexts: List[BaseTask] = []
    children: Dict[str, BaseTask] = {}
    description: str = ""
    completed: bool = False
    shown_completed: bool = False
    position: Tuple[int, int] = None
    is_open: bool = False

    def model_post_init(self, __context):
        super().model_post_init(__context)
        if self.parent is not None:
            if self.name in self.parent.children:
                self.delete()
                raise ValueError(f"Child with name {self.name} already exists in parent {self.parent.name}")
            self.parent.add_child(self)
        for child in self.children.values():
            child.set_parent(self)
        for dep in self.dependencies:
            dep.add_next(self)
        for next in self.nexts:
            next.add_dependency(self)

    def __repr__(self):
        return f"Task(name={self.name}, children={self.children})"

    def __str__(self):
        return self.__repr__()
        
    def get_id(self):
        if self.id is None:
            if self.parent is None:
                self.id = f"{self.name}"
            else:
                self.id = f"{self.parent.get_id()}|{self.name}"
        return self.id

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
        return self.nexts == []
    
    def add_dependency(self, new: BaseTask):
        if new not in self.dependencies:
            if new.level != self.level:
                raise ValueError("Can only add dependencies of the same level")
            self.dependencies.append(new)
            new.add_next(self)
    
    def add_next(self, new: BaseTask):
        if new not in self.nexts:
            if new.level != self.level:
                raise ValueError("Can only add dependencies of the same level")
            self.nexts.append(new)
            new.add_dependency(self)
    
    def add_child(self, new: BaseTask):
        if new.name not in self.children:
            if new.level != self.level + 1:
                raise ValueError("Can only add children with level = parent.level + 1")
            self.children[new.name] = new
            new.set_parent(self)

    def set_parent(self, new: BaseTask):
        if self.parent != new:
            if new.level != self.level - 1:
                raise ValueError("Can only add parents with level = child.level - 1")
            self.parent = new
            new.add_child(self)
    
    def create_dependency(self, name: str):
        return Task(
            level=self.level,
            name=name,
            plan=self.plan,
            parent=self.parent,
            nexts=[self]
        )
    
    def create_next(self, name: str):
        return Task(
            level=self.level,
            name=name,
            plan=self.plan,
            parent=self.parent,
            dependencies=[self]
        )

    def create_child(self, name: str):
        return Task(
            level=self.level + 1,
            name=name,
            plan=self.plan,
            parent=self
        )
    
    def delete(self):
        for dep in self.dependencies:
            dep.nexts.remove(self)
        for next in self.nexts:
            next.dependencies.remove(self)
        for child in self.children.values():
            child.delete()
        if self.parent is not None:
            del self.parent.children[self.name]
        del self

    def get_json(self):
        self_dict = {
            "name": self.name,
            "plan": self.plan.name,
            "dependencies": [dep.name for dep in self.dependencies],
            "nexts": [next.name for next in self.nexts],
            "description": self.description,
            "completed": self.completed
        }
        self_dict["children"] = {
            name: child.get_json()
            for name, child in self.children.items()
        }
        return self_dict