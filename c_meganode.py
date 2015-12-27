# -*- coding: utf-8 -*-
"""
Created on Sun May 11 14:04:35 2014

@author: StackOverflow
( http://stackoverflow.com/questions/2358045/how-can-i-implement-a-tree-in-python-are-there-any-built-in-data-structures-in )
"""

# Copyright (C) by Brett Kromkamp 2011-2014 (brett@youprogramming.com)
# You Programming (http://www.youprogramming.com)
# May 03, 2014




import uuid

def sanitize_id(id):
    return id.strip().replace(" ", "")

# (_ADD, _DELETE, _INSERT) = range(3)
# (_ROOT, _DEPTH, _WIDTH) = range(3)
#
# #Этими классами храним все в базе, выполняем...
# class Node():
#
#     def __init__(self, name, node_val, identifier=None, expanded=True):
#         self.__identifier = (str(uuid.uuid1()) if identifier is None else
#                 sanitize_id(str(identifier)))
#         self.name = name
#         self.node_val = node_val
#         self.expanded = expanded
#         self.__bpointer = None
#         self.__fpointer = []
#
#     def __repr__(self):
#         return str(self.name) + ":" + str(self.node_val)
#
#     @property
#     def identifier(self):
#         return self.__identifier
#
#     @property
#     def bpointer(self):
#         return self.__bpointer
#
#     @bpointer.setter
#     def bpointer(self, value):
#         if value is not None:
#             self.__bpointer = sanitize_id(value)
#
#     @property
#     def fpointer(self):
#         return self.__fpointer
#
#     def update_fpointer(self, identifier, mode=_ADD):
#         if mode is _ADD:
#             self.__fpointer.append(sanitize_id(identifier))
#         elif mode is _DELETE:
#             self.__fpointer.remove(sanitize_id(identifier))
#         elif mode is _INSERT:
#             self.__fpointer = [sanitize_id(identifier)]
#
#     def get_child_list(self):
#         return self.__fpointer
#
#     def get_clone(self, omit_values = 1):
#         new_node = None
#         if omit_values:
#             #This is the actual call
#             new_node = Node(self.name, None, self.__identifier, self.expanded)
#         else:
#             if hasattr(self.node_val, "get_clone"):
#                 new_node = Node(self.name, self.node_val.get_clone(), self.__identifier, self.expanded)
#             else:
#                 new_node = Node(self.name, self.node_val, self.__identifier, self.expanded)
#         return new_node
#
#
# class Tree():
#
#     def __init__(self):
#         self.nodes = []
#
#     def __repr__(self):
#         s_repr = "Tree: \n"
#         for n_i in self.nodes:
#             s_repr += str(n_i) + "\n"
#         return s_repr
#
#     def get_index(self, position):
#         for index, node in enumerate(self.nodes):
#             if node.identifier == position:
#                 break
#         return index
#
#     def create_node(self, name, node_val, identifier=None, parent=None):
#         node = Node(name, node_val, identifier)
#         self.nodes.append(node)
#         self.__update_fpointer(parent, node.identifier, _ADD)
#         node.bpointer = parent
#         return node
#
#     def add_node(self, node, parent=None):
#         self.nodes.append(node)
#         self.__update_fpointer(parent, node.identifier, _ADD)
#         node.bpointer = parent
#
#     def show(self, position, level=_ROOT):
#         queue = self[position].fpointer
#         if level == _ROOT:
#             print("{%s} [{%s}]"%(self[position].name,self[position].identifier))
#         else:
#             tabs = "\t"*level
#             print("%s {%s} [{%s}]"%(tabs, self[position].name,self[position].identifier))
#         if self[position].expanded:
#             level += 1
#             for element in queue:
#                 self.show(element, level)  # recursive call
#
#     def direct_childs(self, position):
#         queue = self[position].fpointer
#         if self[position].expanded:
#             for element in queue:
#                 yield element
#
#     def expand_tree(self, position, mode=_DEPTH):
#         # Python generator. Loosly based on an algorithm from 'Essential LISP' by
#         # John R. Anderson, Albert T. Corbett, and Brian J. Reiser, page 239-241
#         yield position
#         queue = self[position].fpointer
#         while queue:
#             yield queue[0]
#             expansion = self[queue[0]].fpointer
#             if mode is _DEPTH:
#                 queue = expansion + queue[1:]  # depth-first
#             elif mode is _WIDTH:
#                 queue = queue[1:] + expansion  # width-first
#
#     def is_branch(self, position):
#         return self[position].fpointer
#
#     def __update_fpointer(self, position, identifier, mode):
#         if position is None:
#             return
#         else:
#             self[position].update_fpointer(identifier, mode)
#
#     def get_parent(self, node_i):
#         #TODO: add expand - from top
#         #Inefficient - mine. For small applications only.
#         lop = 1
#         k = 0
#         par = None
#         identifier = node_i.identifier
#         while lop:
#             n_i = self.nodes[k]
#             childs = n_i.get_child_list()
#             if identifier in childs:
#                 lop = 0
#                 par = n_i
#             elif k>=(len(self.nodes)-1):
#                 lop = 0
#             k+=1
#         return par
#
#
#     def __update_bpointer(self, position, identifier):
#         self[position].bpointer = identifier
#
#     def __getitem__(self, key):
#         return self.nodes[self.get_index(key)]
#
#     def __setitem__(self, key, item):
#         self.nodes[self.get_index(key)] = item
#
#     def __len__(self):
#         return len(self.nodes)
#
#     def __contains__(self, identifier):
#         return [node.identifier for node in self.nodes
#                 if node.identifier is identifier]
#
#     def get_clone(self, omit_values = 1):
#         #with omit_values = 1 this is a sceleton with same IDs
#         new_tree = Tree()
#         for node_i in self.nodes:
#             new_node = node_i.get_clone(omit_values)
#             parent_node = self.get_parent(node_i)
#             if parent_node:
#                 new_tree.add_node(new_node, parent_node.identifier)
#             else:
#                 new_tree.add_node(new_node)
#         return new_tree

#А этот класс оказался удобней для интерфейса
class gui_Node(object):

    def __init__(self, name, parent=None):
        self._name = name
        self._childrenNodes = []
        self._parentNode = parent
        if parent is not None:
            parent.addChild(self)

    def typeInfo(self):
        return "NODE"

    def addChild(self, child):
        self._childrenNodes.append(child)

    def insertChild(self, position, child):
        if position < 0 or position > len(self._childrenNodes):
            return False
        self._childrenNodes.insert(position, child)
        child._parentNode = self
        return True

    def removeChild(self, position):
        if position < 0 or position > len(self._childrenNodes) or len(self._childrenNodes)==0:
            return False
        child = self._childrenNodes.pop(position)
        child._parentNode = None
        return True

    def name(self):
        return self._name

    def setName(self, name):
        self._name = name

    def child(self, row):
        return self._childrenNodes[row]

    def childCount(self):
        return len(self._childrenNodes)

    def iter_all_children(self):
        for ch_i in self._childrenNodes:
            yield ch_i
            yield ch_i.iter_all_children()

    def get_parentNode(self):
        return self._parentNode

    def row(self):
        if self._parentNode is not None:
            return self._parentNode._childrenNodes.index(self)

    def log(self, tabLevel=-1):
        output     = ""
        tabLevel += 1
        for i in range(tabLevel):
            output += "\t"
        output += "|------" + self._name + "\n"
        for child in self._childrenNodes:
            output += child.log(tabLevel)
        tabLevel -= 1
        return output

    def __repr__(self):
        return self.log()


if __name__ == "__main__":

    tree = Tree()
    tree.create_node(name = "Harry", node_val = "this is Harry", identifier = "harry")  # root node
    tree.create_node(name = "Jane", node_val = "this is Jane, daughter of Harry", identifier = "jane", parent = "harry")
    tree.create_node(name = "Bill", node_val = "this is Bill, son of Harry", identifier = "bill", parent = "harry")
    tree.create_node(name = "Joe", node_val = "this is Joe, son of Jane", identifier = "joe", parent = "jane")
    tree.create_node(name = "Diane",node_val = "this is Diane, daughter of Jane", identifier = "diane", parent = "jane")
    tree.create_node(name = "George", node_val = "this is George, son of Diane", identifier = "george", parent = "diane")
    tree.create_node(name = "Mary", node_val = "this is Mary, daughter of Diane", identifier = "mary", parent = "diane")
    tree.create_node(name = "Jill", node_val = "this is Jill, son of George", identifier = "jill", parent = "george")
    tree.create_node(name = "Carol", node_val = "this is Carol, daughter of Jill", identifier = "carol", parent = "jill")
    tree.create_node(name = "Grace", node_val = "this is Grace, daughter of Bill", identifier = "grace", parent = "bill")
    tree.create_node(name = "Mark", node_val = "this is Mark, son of Jane", identifier = "mark", parent = "jane")
    tree.create_node(name = "Harry The Second", node_val = "this is Harry", identifier = "harry2")  # 2nd root node
    tree.create_node(name = "Jane2", node_val = "this is Jane, daughter of Harry The Second", identifier = "jane2", parent = "harry2")

#    print("="*80)
#    tree.show("harry")
    new_tree = tree.get_clone(0)
    print("="*80)
    for node in new_tree.nodes:
        print(node)
        print("parent: " + str(tree.get_parent(node)))
#    print("="*80)
#    for node in tree.expand_tree("diane", mode = _DEPTH):
#        print(tree[node])
#    print("="*80)
#    ex1 = "george"
#    print("Direct childs of " + ex1)
#    for ch_node in tree.direct_childs(ex1):
#        print(tree[ch_node])
#    print("="*80)
#    ex1 = "diane"
#    print("Direct childs of " + ex1)
#    for ch_node in tree.direct_childs(ex1):
#        print(tree[ch_node])
#    print("="*80)
#    ex1 = "harry"
#    print("Direct childs of " + ex1)
#    for ch_node in tree.direct_childs(ex1):
#        print(tree[ch_node])
#    print("="*80)
#    ex1 = "bill"
#    print("Direct childs of " + ex1)
#    for ch_node in tree.direct_childs(ex1):
#        print(tree[ch_node])
#    print("="*80)
#    ex1 = "mark"
#    print("Direct childs of " + ex1)
#    for ch_node in tree.direct_childs(ex1):
#        print(tree[ch_node])
#    print("="*80)
#    for node in tree.get_all_branch_nodes():
#        print(node)
#    print("="*80)    
#    ex1 = "harry"
#    print("Test with getting a parent")
#    tree.get_parent_id(ex1)
#    print("="*80)    
#    ex1 = "jane"
#    print("Test with getting a parent")
#    tree.get_parent_id(ex1)