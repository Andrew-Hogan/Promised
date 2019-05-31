"""Let's get excited about making some boilerplate properties!"""
import re
from typing import Union, List


def name_to_snake_case(name):
    """Converts a name from CamelCase to snake_case."""
    return re.sub('((?!^)(?<!_)[A-Z][a-z]+|(?<=[a-z0-9])[A-Z])', r'_\1', name).lower()


class _BasePropertyAccess(object):
    def __init__(self, name: Union[str, None] = None, doc: Union[str, None] = None):
        self._name = name  # Name of hidden attribute in source class. (set in keeper)
        self.doc = doc  # Doc of attribute in source class.

    def keeper(self, *_):
        raise NotImplementedError

    def getter(self, *_):
        raise NotImplementedError

    def setter(self, *_):
        raise NotImplementedError

    def deleter(self, *_):
        raise NotImplementedError

    def _default_getter(self, obj):
        """Use getattr(obj, self._name) as default getter if no getter decorated nor provided at init."""
        try:
            return getattr(obj, self._name)
        except TypeError:
            raise

    def _default_setter(self, obj, value):
        """Use setattr(obj, self._name, value) as default setter if no setter decorated nor provided at init."""
        try:
            setattr(obj, self._name, value)
        except TypeError:
            raise

    def _default_deleter(self, obj):
        """Use delattr(obj, self._name) as default deleter if no deleter decorated nor provided at init."""
        try:
            delattr(obj, self._name)
        except AttributeError:
            pass
        except TypeError:
            raise

    def __call__(self, func):
        self.keeper(func)
        return self

    def __get__(self, instance, owner):
        try:
            return self._getter(instance)
        except AttributeError:
            if instance is None:
                return self
            try:
                self._keeper(instance)
            except TypeError:
                raise AttributeError("Promised property keeper not set.")
        except TypeError:
            if self._name is None and self._keeper:
                raise AttributeError("Promised property private _name variable set to None. [Was a keeper provided?]")
            else:
                raise AttributeError("Promised property keeper not set.")
        return self._getter(instance)

    def __set__(self, instance, value):
        try:
            self._setter(instance, value)
        except TypeError:
            if self._name is None:
                raise AttributeError("Promised property private _name variable set to None. [Was a keeper provided?]")
            else:
                raise AttributeError("Promised property does not have a setter.")

    def __delete__(self, obj):
        try:
            self._deleter(obj)
        except TypeError:
            if self._name is None:
                raise AttributeError("Promised property private _name variable set to None. [Was a keeper provided?]")
            else:
                raise AttributeError("Promised property does not have a deleter.")

    def __repr__(self, *_, **__):
        return f"<{self.__class__} hidden attribute {self._name} id #{id(self)}>"

    __str__ = __repr__


class promise(_BasePropertyAccess):
    """
    A flexible cached property with get/set/del/init/cached-mapping capabilities for inter-property relationships.

    Let's start with what this is not: it's not an async Promise like those used in javascript - it won't introduce
    anything you haven't already used in Python, and using the properties it creates will feel just like an @property.

    What is a promise? A promise is a lazily evaluated property. Functionally, it is very similar to the @property
    decorator, and its usage-syntax reflects that. The key usage difference is that by default its first-wrapped
    method is its promise keeper instead of its getter.

    What is a promise keeper? The keeper should set the hidden attribute this descriptor protects in the event of an
    AttributeError from the getter method. (Meaning the hidden attribute has not yet been set.)

    Why have the keeper be the initial decorated method by default? As a promise already handles AttributeErrors from
    unbound attributes, a promise will often not need a complicated getter. With that in mind, a promise will create
    its own getter method if none is ever provided, that being lambda x: getattr(x, self._name).

    What is self._name? If no getter method is provided, self._name will be used as a key for accessing the attribute
    set within the keeper method. self._name is set (in order of preference) first as the name passed in __init__; and,
    if that is None (default), then it is set as the keeper method's __name__ with a leading underscore. (
        "_" + keeper.__name__
    )

    Why have a keeper and a default getter? Because I found myself doing this too often:
        @property
        def property_public_name(self):
            '''Why am I typing the same lines with tiny changes in every project all the time?'''
            try:
                return self._property_public_name_with_leading_underscore
            except AttributeError:
                self._property_public_name_with_leading_underscore = self._method_to_calculate_property()
            return self._property_public_name_with_leading_underscore

    Now, it looks like this:
        @promise
        def property_public_name(self):
            '''Now this is promising!'''
            self._property_public_name_with_leading_underscore = self._method_to_calculate_property()

    In keeping with that format and idea, we could have had the promise keeper simply return the value and set the
    attribute to self._name from the promise (or as an attribute in the promise itself), shaving off the need to type
    'self._name_of_property =' in every keeper, but time has shown that allowing keeper functions to be both flexible
    and explicit is the way to go - and has given rise to useful property patterns.

    For example:
        def _set_associated_maps(self):
            attr_one, attr_two, attr_three = ATTR_ONE_NAME, ATTR_TWO_NAME, ATTR_THREE_NAME
            map_one = {}
            map_two = {}
            map_three = {}

            for thing in self:
                for this_map, this_name in zip((map_one, map_two, map_three), (attr_one, attr_two, attr_three)):
                    try:
                        this_value = getattr(thing, this_name)
                    except AttributeError:
                        continue
                    try:
                        previous = this_map[this_value]
                        previous.add(thing)
                    except KeyError:
                        this_map.update({this_value: {thing}})

            self._map_one = map_one
            self._map_two = map_two
            self._map_three = map_three

        map_one = promise(_set_associated_maps, name='_map_one')
        map_two = promise(_set_associated_maps, name='_map_two')
        map_three = promise(_set_associated_maps, name='_map_three')

    This results in a group of properties which will all be set at the time that the first among them is accessed. If
    iterating through the shared source of multiple properties is an expensive operation, it may be worthwhile to
    combine a group of promise keepers together into one method.
    """
    def __init__(self, keeper: callable = None, *,
                 name: str = None,
                 doc: str = None,
                 getter: Union[bool, callable] = None,
                 deleter: Union[bool, callable] = None,
                 setter: Union[bool, callable] = None):
        """
        :Parameters:
            :param keeper: Method to create value of property when accessed with AttributeError.
            :param name: Private attribute name to access stored property value or "_" + keeper.__name__ if None.
            :param doc: Docstring for property value or keeper.__doc__ if None.
            :param getter: Getter for accessing stored property value, getattr(obj, self._name) if None,
                or disabled if False.
            :param deleter: Deleter for clearing stored property value, delattr(obj, self._name) if None,
                or disabled if False.
            :param setter: Setter for changing stored property value, setattr(object, self._name, value) if None,
                or disabled if False.
        """
        super().__init__(name, doc)
        self.keeper(keeper)
        self.getter(getter)
        self.setter(setter)
        self.deleter(deleter)

    def keeper(self, _keeper):
        if _keeper:
            self._attribute_name_of_class_instance = name_to_snake_case(_keeper.__qualname__.split(".")[-2])
            self._name = "_" + _keeper.__name__ if self._name is None else self._name  # First pref is init name arg
            self.__doc__ = _keeper.__doc__ if self.doc is None else self.doc  # First pref is init doc arg
        else:
            if self.doc:
                self.__doc__ = self.doc
        self._keeper = _keeper
        return self

    def getter(self, _getter):
        self._getter = _getter if _getter is not None else self._default_getter
        return self

    def setter(self, _setter):
        self._setter = _setter if _setter is not None else self._default_setter
        return self

    def deleter(self, _deleter):
        self._deleter = _deleter if _deleter is not None else self._default_deleter
        return self


class linked(_BasePropertyAccess):
    """
    A flexible cached property with get/set/del/init/dependant capabilities for inter-property relationships.

    Usage:
        For most usage, see promise decorator.

        Besides a default getter, this decorator has a default deleter & setter as well.

        Use @property_name.linked above any other property to call that property's delete method whenever a linker of
        this property is called. (can be placed above getter / keeper / deleter / setter - needs to be done only once.)

        Linkers of this property are by default deleter and setter, but if linkers (tuple) is passed at init,
            the default deleter and setter will not be linkers. In that case, only methods decorated by the linker
            method will trigger linked property updates.

        Pass "False" for deleter or setter if no-delete / no-write behavior desired.

    Defaults:
        deleter: lambda x: delattr(x, self._name)
        setter: lambda x, y: setattr(x, self._name, y)
        getter: lambda x: getattr(x, self._name)

        linkers: ('deleter', 'setter')
    """
    def __init__(self, keeper: callable = None, *,
                 name: str = None,
                 doc: str = None,
                 getter: Union[bool, callable] = None,
                 deleter: Union[bool, callable] = None,
                 setter: Union[bool, callable] = None,
                 linkers: Union[List[str], str] = None,
                 chain: bool = False):
        """
        :Parameters:
            :param keeper: Method to create value of property when accessed with AttributeError.
            :param name: Name to access stored property value using by default or "_" + keeper.__name__ if None.
            :param doc: Docstring for property value or keeper.__doc__ if None.
            :param getter: Getter for accessing stored property value, getattr(obj, self._name) if None,
                or disabled if False.
            :param deleter: Deleter for clearing stored property value, delattr(obj, self._name) if None,
                or disabled if False.
            :param setter: Setter for changing stored property value, setattr(object, self._name, value) if None,
                or disabled if False.
            :param linkers: Methods which should cause a refresh in linked properties -
                default equivalent to ["deleter", "setter"]. Disabled if value is [].
            :param chain: True if this property is a source of property dependencies external to the instance's class.
                If True, this property should only ever return instances of a single class.
        """
        super().__init__(name, doc)
        self._linked = set()  # Linked properties
        self._external_linked = Member(lambda *_: set())  # External dependent properties to be updated in another class upon change.
        self._chain = chain  # Boolean - is chain dependency source?
        self._internal_to_chain = Member(lambda *_: set())  # Dependent properties to be updated from this property's value's class upon change.
        self._most_recent_internal = None  # Tracks most recent chain-decorated methods.
        old_linker = self.linker
        if linkers is not None:
            self.linker = lambda _: None  # Linker decorated temporarily removed to prevent default linkers if linkers.
        self._most_recent_linker = None  # Tracks most recent link-decorated methods.
        self.keeper(keeper)
        self.getter(getter)
        if setter is not False:
            self.setter(setter)
        else:
            self._setter = None
        if deleter is not False:
            self.deleter(deleter)
        else:
            self._deleter = None
        if linkers is not None:
            self._set_explicit_linkers(linkers, old_linker)

    def keeper(self, _keeper):
        """Set keeper and _name / doc from init or decoration."""
        self._most_recent_linker = self._linked_keeper
        self._attribute_name_of_class_instance = _keeper if _keeper is None else name_to_snake_case(
            _keeper.__qualname__.split(".")[-2]
        )
        if _keeper:
            self._name = "_" + _keeper.__name__ if self._name is None else self._name  # First pref is init name arg
            self.__doc__ = _keeper.__doc__ if self.doc is None else self.doc  # First pref is init doc arg
        else:
            if self.doc:
                self.__doc__ = self.doc
        if self._chain:
            self._chain_keeper = _keeper
            self._keeper = self.chain_keeper
        else:
            self._keeper = _keeper
        return self

    def _linked_keeper(self, instance):
        """Called before keeper if keeper is linker. (Not default - will delete dependents on every default call.)"""
        self._hidden_keeper(instance)
        self._update_linked(instance)

    def chain_keeper(self, instance):
        self._chain_keeper(instance)
        setattr(self._getter(instance), self._attribute_name_of_class_instance, instance)

    def getter(self, _getter):
        """Set getter if provided else default getter of getattr(x, self._name)."""
        self._most_recent_linker = self._linked_getter
        self._getter = _getter if _getter is not None else self._default_getter
        return self

    def _linked_getter(self, instance):
        """Called before getter if getter is linker. (Not default - will delete dependents on every access.)"""
        try:
            self._hidden_getter(instance)
        except AttributeError:
            raise
        else:
            self._update_linked(instance)

    def setter(self, _setter):
        """Set setter if provided else default setter (with linked-deletion calls if no init linkers)."""
        self._most_recent_linker = self._linked_setter
        if _setter is None:
            self._setter = self._default_setter
            if self._chain:
                self._chain_setter = self._setter
                self._setter = self.chain_setter
            self.linker(self)
        else:
            self._setter = _setter
            if self._chain:
                self._chain_setter = self._setter
                self._setter = self.chain_setter
        return self

    def _linked_setter(self, instance, value):
        """Called before setter if setter is linker. (True if no linkers at init and default setter.)"""
        self._hidden_setter(instance, value)
        self._update_linked(instance)

    def chain_setter(self, instance, value):
        try:
            existing = self._getter(instance)
        except AttributeError:
            pass
        else:
            try:
                delattr(existing, self._attribute_name_of_class_instance)
            except AttributeError:
                pass
        self._chain_setter(instance, value)
        setattr(self._getter(instance), self._attribute_name_of_class_instance, instance)

    def deleter(self, _deleter):
        """Set deleter if provided else access-safe default deleter (with linked-deletion calls if no init linkers.)"""
        self._most_recent_linker = self._linked_deleter
        if _deleter is None:
            self._deleter = self._default_deleter
            if self._chain:
                self._chain_deleter = self._deleter
                self._deleter = self.chain_deleter
            self.linker(self)
        else:
            self._deleter = _deleter
            if self._chain:
                self._chain_deleter = self._deleter
                self._deleter = self.chain_deleter
        return self

    def _linked_deleter(self, obj):
        """Called before deleter if deleter is linker. (True if no linkers at init and default deleter.)"""
        self._hidden_deleter(obj)
        self._update_linked(obj)

    def chain_deleter(self, obj):
        try:
            existing = self._getter(obj)
        except AttributeError:
            pass
        else:
            try:
                delattr(existing, self._attribute_name_of_class_instance)
            except AttributeError:
                pass
        self._chain_deleter(obj)

    def _update_linked(self, obj):
        """Delete linked properties for value refresh."""
        old_deleter = self._deleter
        self._deleter = lambda _: None  # Temporarily remove deleter to prevent recursion & undoing value set.
        for linked_property in self._linked:
            try:
                linked_property.__delete__(obj)
            except AttributeError:
                pass
        for linked_instance_name, linked_instance_properties in self._external_linked.items():
            try:
                instance = getattr(obj, linked_instance_name)
            except AttributeError:
                pass
            else:
                for linked_property in linked_instance_properties:
                    try:
                        linked_property.__delete__(instance)
                    except AttributeError:
                        pass
        self._deleter = old_deleter

    def linker(self, _linker):
        """Links explicitly decorated linkers and default linkers (if no linkers or del / set passed in init)."""
        if isinstance(_linker, str):
            old_name = f"_{_linker}"
            new_func = getattr(self, f"_linked{old_name}")
        else:
            new_func = self._most_recent_linker
            old_name = new_func.__name__[7:]
        setattr(self, f"_hidden{old_name}", getattr(self, old_name))
        setattr(self, old_name, new_func)
        return _linker  # Should be self

    def _set_explicit_linkers(self, linkers, old_linker):
        """Set explicit linkers at end of init and restore linker decorator."""
        if isinstance(linkers, str):
            self._linker(linkers)
        else:
            for linker in linkers:
                self._linker(linker)
        self.linker = old_linker

    def _linker(self, public_name):
        """Links explicitly passed linkers from init."""
        setattr(self, f"_hidden_{public_name}", getattr(self, f"_{public_name}"))
        setattr(self, f"_{public_name}", getattr(self, f"_linked_{public_name}"))

    def linked(self, linked_attribute):  # TODO: Add optional args for designating auto-created property attributes? (e.g. _name)
        """Adds property to set of linked properties to be updated (deleted) when a linker-method is called."""
        try:
            name = linked_attribute._attribute_name_of_class_instance
        except AttributeError:
            linked_attribute = linked(linked_attribute)
            name = linked_attribute._attribute_name_of_class_instance
            self._linked.add(linked_attribute)
        if name != self._attribute_name_of_class_instance:
            self._external_linked[name].add(linked_attribute)
        else:
            self._linked.add(linked_attribute)
        return linked_attribute

    def chain(self, linked_property_name):  # TODO: Add optional args for designating auto-created property attributes? (e.g. _name)
        """Adds property to set of linked properties to be updated (deleted) when a linker-method is called."""
        self._most_recent_internal = linked_property_name
        if not hasattr(self, "_internal_chain_keeper"):
            self._internal_chain_keeper = self._keeper
            self._keeper = self.internal_chain_keeper
        return self._setup_internal_chain

    def _setup_internal_chain(self, linked_attribute):  # TODO: Currently assumes return from this property's keeper will only ever be one class.
        linked_property_name = self._most_recent_internal
        try:
            _ = linked_attribute._attribute_name_of_class_instance
        except AttributeError:
            linked_attribute = linked(linked_attribute)
        self._internal_to_chain[linked_property_name].add(linked_attribute)
        return linked_attribute

    def internal_chain_keeper(self, instance):
        self._internal_chain_keeper(instance)
        to_chain = self._getter(instance).__class__
        for property_key, chained_attributes in self._internal_to_chain.items():
            this_property = to_chain.__dict__[property_key]
            for attribute in chained_attributes:
                this_property.linked(attribute)
        self._keeper = self._internal_chain_keeper


class Member(dict):
    """
    A map of cached properties per input key which will cache a property for that key when first accessed.

    What is a Member? It is a mapping instance with similar usage to the @promise decorator which will call:
        self._getter(key, *self._args, **self._kwargs)
    and set the mapped value of key to the return from that call if key is not already mapped, and will always return
    the mapped value of that key.

    Why? This is very similar to the need memoization fulfills, but I wanted to treat these cached values as if they
    were any other attribute in a mapping property and planned to use a small set of possible inputs to access them
    multiple times.

    As they could potentially change after being initially set just like @promise properties, it could have been wiser
    to set the values as a promise within the input objects - but, as the attribute was purely for functions within
    the calling instance, this was a useful tool.

    What is self._getter? self._getter is the first argument in __init__ - it should take key as an argument, and return
    the calculated value for that key. Additionally, the optional *args and **kwargs from __init__ are provided as
    arguments to self._getter. (if provided)

    This gives rise to some interesting patterns for similar attributes as well, for example:

        def _children_of_parent_with_attribute_value(self, parent, child_attribute_value):
            return self.parent_children_map[parent] & self.attribute_value_to_set_of_objects_map[child_attribute_value]

        @promise
        def homeless_children(self):
            self._homeless_children = Member(self._children_of_parent_with_attribute_value, "homeless")

        @promise
        def adult_children(self):
            self._adult_children = Member(self._children_of_parent_with_attribute_value, "The White House")

    Getting all homeless children of an object would then be a readily available attribute as
    self.homeless_children[object], and any inner workings for finding and caching those matches is handled by the
    promise and Member decorators. Meanwhile, no calculations for unnecessary properties or members are done.
    """
    def __init__(self, getter, *args, **kwargs):
        super().__init__()
        self._args = args
        self._kwargs = kwargs
        self._getter = getter

    def __missing__(self, key):
        value = self._getter(key, *self._args, **self._kwargs)
        self.update({key: value})
        return value
