"""Let's get excited about making some boilerplate properties!"""
import re
from typing import Union, List


def name_to_snake_case(name):
    """Converts a name from CamelCase to snake_case."""
    return re.sub('((?!^)(?<!_)[A-Z][a-z]+|(?<=[a-z0-9])[A-Z])', r'_\1', name).lower()


class promise(object):
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
    def __init__(self, keeper=None, name=None, doc=None, getter=None, deleter=None, setter=None):
        self._name = name
        self.doc = doc
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
            self._name = self._name if self._name is not None else "_broken_promise"
            if self.doc:
                self.__doc__ = self.doc
        self._keeper = _keeper
        return self

    def setter(self, _setter):
        self._setter = _setter
        return self

    def getter(self, _getter):
        self._getter = _getter if _getter is not None else lambda x: getattr(x, self._name)
        return self

    def deleter(self, _deleter):
        self._deleter = _deleter
        return self

    def __call__(self, func):
        self.keeper(func)
        return self

    def __get__(self, instance, owner):
        try:
            return self._getter(instance)
        except AttributeError:
            if instance is None:
                return self
            assert self._keeper is not None, AttributeError("Promised property keeper not set.")
            self._keeper(instance)
        return self._getter(instance)

    def __set__(self, instance, value):
        assert self._setter is not None, AttributeError("Promised property does not have a setter.")
        self._setter(instance, value)

    def __delete__(self, obj):
        assert self._deleter is not None, AttributeError("Promised property does not have a deleter.")
        self._deleter(obj)

    def __repr__(self, *_, **__):
        return f"<promised hidden attribute {self._name} id #{id(self)}>"

    __str__ = __repr__


class linked(object):
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
        self._linked = set()  # Linked properties
        self._external_linked = {}  # External dependent properties to be updated in another class upon change.
        self._chain = chain  # Boolean - is chain dependency source?
        self._internal_to_chain = {}  # Dependent properties to be updated from this property's value's class upon change.
        self._most_recent_internal = None  # Tracks most recent chain-decorated methods.
        old_linker = self.linker
        if linkers is not None:
            self.linker = lambda _: None  # Linker decorated temporarily removed to prevent default linkers if linkers.
        self._most_recent_linker = None  # Tracks most recent link-decorated methods.
        self._name = name  # Name of hidden attribute in source class. (set in keeper)
        self.doc = doc  # Doc of attribute in source class.
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
        self._attribute_name_of_class_instance = _keeper if _keeper is None else name_to_snake_case(_keeper.__qualname__.split(".")[-2])
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
        self._getter = _getter if _getter is not None else lambda x: getattr(x, self._name)
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
            self._setter = lambda x, y: setattr(x, self._name, y)
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

    def _default_deleter(self, obj):
        """Use delattr(obj, self._name) as default deleter if no deleter decorated nor provided at init."""
        try:
            delattr(obj, self._name)
        except AttributeError:
            pass

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
                # print(f"Error updating external linked for linked {linked_instance_name} in {obj}: {e}")
            else:
                for linked_property in linked_instance_properties:
                    try:
                        linked_property.__delete__(instance)
                        # print(f"Deleted property {linked_property} in external {instance}!")
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
            try:
                self._external_linked[name].add(linked_attribute)
            except KeyError:
                self._external_linked.update({name: {linked_attribute}})
        else:
            self._linked.add(linked_attribute)
        return linked_attribute

    def chain(self, linked_property_name):  # TODO: Add optional args for designating auto-created property attributes? (e.g. _name)
        """Adds property to set of linked properties to be updated (deleted) when a linker-method is called."""
        print(f"Chaining {linked_property_name} internally")
        self._most_recent_internal = linked_property_name
        if not hasattr(self, "_internal_chain_keeper"):
            self._internal_chain_keeper = self._keeper
            self._keeper = self.internal_chain_keeper
        return self._setup_internal_chain

    def _setup_internal_chain(self, linked_attribute):  # TODO: Currently assumes return from this property's keeper will only ever be one class.
        linked_property_name = self._most_recent_internal
        print(f"Chaining {linked_property_name} externally")
        try:
            _ = linked_attribute._attribute_name_of_class_instance
        except AttributeError:
            linked_attribute = linked(linked_attribute)
        try:
            self._internal_to_chain[linked_property_name].add(linked_attribute)
        except KeyError:
            self._internal_to_chain.update({linked_property_name: {linked_attribute}})
        return linked_attribute

    def internal_chain_keeper(self, instance):
        self._internal_chain_keeper(instance)
        to_chain = self._getter(instance).__class__
        for property_key, chained_attributes in self._internal_to_chain.items():
            this_property = to_chain.__dict__[property_key]
            for attribute in chained_attributes:
                this_property.linked(attribute)
        self._keeper = self._internal_chain_keeper

    def __call__(self, func):
        self.keeper(func)
        return self

    def __get__(self, instance, owner):
        try:
            return self._getter(instance)
        except AttributeError:
            if instance is None:
                return self
            assert self._keeper is not None, AttributeError("Linked property keeper not set.")
            self._keeper(instance)
        return self._getter(instance)

    def __set__(self, instance, value):
        self._setter(instance, value)

    def __delete__(self, obj):
        self._deleter(obj)

    def __repr__(self, *_, **__):
        return f"<Linked hidden attribute {self._name} id #{id(self)}>"

    __str__ = __repr__


class Member(object):
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
        self._members = {}
        self._args = args
        self._kwargs = kwargs
        self._getter = getter

    def __getitem__(self, key):
        try:
            return self._members[key]
        except KeyError:
            self._members.update({key: self._getter(key, *self._args, **self._kwargs)})
        return self._members[key]

    def __setitem__(self, key, value):
        return self._members.__setitem__(key, value)

    def __delitem__(self, key):
        return self._members.__delitem__(key)

    def __contains__(self, item):
        return item in self._members

    def __len__(self):
        return len(self._members)

    def items(self):
        return self._members.items()

    def values(self):
        return self._members.values()

    def keys(self):
        return self._members.keys()

    def __repr__(self, *_, **__):
        return f"<promised member attribute for {self._getter.__name__} with id #{id(self)}>"

    def __str__(self, *_, **__):
        return str(self._members)


_TEST_VALUE = "Set by promise keeper"


class _TestClass(object):
    """This is a test class for promises & Members. I don't know what more you're expecting."""
    @promise
    def test_attribute(self):
        assert self.__class__ is _TestClass, "Keeper method not bound to instance of _TestClass."
        assert not hasattr(self, "_test_attribute"), "Keeper method called despite existing self._test_attribute."
        self._test_attribute = _TEST_VALUE
        assert self._test_attribute == _TEST_VALUE, "self._test_attribute not set to _TEST_VALUE in keeper."

    @test_attribute.deleter
    def test_attribute(self):
        assert self.__class__ is _TestClass, "Deleter method not bound to instance of _TestClass."
        del self._test_attribute
        assert not hasattr(self, "_test_attribute"), "self._test_attribute not deleted in deleter."

    @test_attribute.setter
    def test_attribute(self, value):
        assert self.__class__ is _TestClass, "Setter method not bound to instance of _TestClass."
        self._test_attribute = value
        assert self._test_attribute == value, "self._test_attribute not set to value in setter."

    @promise
    def test_member(self):
        assert self.__class__ is _TestClass, "Keeper method for member not bound to instance of _TestClass."
        self._test_member = Member(lambda x: x * x)

    def _calc_test_member(self, key):
        assert self.__class__ is _TestClass, "Getter method for method member not bound to instance of _TestClass."
        return self.test_member[self.test_member[key]]

    @promise
    def test_member_from_method(self):
        assert self.__class__ is _TestClass, "Keeper method for method member not bound to instance of _TestClass."
        self._test_member_from_method = Member(self._calc_test_member)

    def __repr__(self, *_, **__):
        return f"<{self.__class__.__name__} object {id(self)}>"

    __str__ = __repr__


_TEST_VALUE_TWO = "Set by linked update"


class _TestClassTwo(object):
    """This is a test class for linked promises. I don't know what more you're expecting."""
    @linked
    def test_linked_link(self):
        assert self.__class__ is _TestClassTwo, "Linked link keeper method not bound to instance of _TestClassTwo."
        assert not hasattr(self, "_test_linked_link"), ("Linked link keeper method called "
                                                        "despite existing self._test_linked_link.")
        self._test_linked_link = _TEST_VALUE
        assert self._test_linked_link == _TEST_VALUE, ("self._test_linked_link not set to _TEST_VALUE "
                                                       "in linked link keeper.")

    @test_linked_link.linked
    @linked
    def test_link(self):
        assert self.__class__ is _TestClassTwo, "Link keeper method not bound to instance of _TestClassTwo."
        assert not hasattr(self, "_test_link"), "Link keeper method called despite existing self._test_link."
        self._test_link = _TEST_VALUE
        assert self._test_link == _TEST_VALUE, "self._test_link not set to _TEST_VALUE in link keeper."

    @test_link.linked
    @test_linked_link.setter
    def test_linked_link(self, value):
        assert self.__class__ is _TestClassTwo, "Linked setter method not bound to instance of _TestClassTwo."
        self._test_linked_link = value
        assert self._test_linked_link == value, "self._test_linked_link not set to value in setter."

    @promise
    def test_attribute(self):
        assert self.__class__ is _TestClassTwo, "Keeper method not bound to instance of _TestClassTwo."
        assert not hasattr(self, "_test_attribute"), "Keeper method called despite existing self._test_attribute."
        self._test_attribute = self.test_link
        assert self._test_attribute == self.test_link, "self._test_attribute not set to self.test_link in keeper."

    test_link.linked(test_attribute)

    @test_attribute.deleter
    def test_attribute(self):
        assert self.__class__ is _TestClassTwo, "Deleter method not bound to instance of _TestClassTwo."
        del self._test_attribute
        assert not hasattr(self, "_test_attribute"), "self._test_attribute not deleted in deleter."

    @test_attribute.setter
    def test_attribute(self, value):
        assert self.__class__ is _TestClassTwo, "Setter method not bound to instance of _TestClassTwo."
        self._test_attribute = value
        assert self._test_attribute == value, "self._test_attribute not set to value in setter."


_TEST_LENGTH_INIT = 2
_TEST_LENGTH_A = 5
_TEST_AREA_INIT = _TEST_LENGTH_INIT ** 2
_TEST_VOLUME_INIT = _TEST_AREA_INIT * _TEST_LENGTH_INIT
_TEST_AREA_A = _TEST_LENGTH_A ** 2
_TEST_VOLUME_A_INIT_DEPTH = _TEST_AREA_A * _TEST_LENGTH_INIT
_TEST_VOLUME_A = _TEST_AREA_A * _TEST_LENGTH_A


class _TestLine(object):
    """This is a test class for linked promises. I don't know what more you're expecting."""
    def __init__(self, length=_TEST_LENGTH_INIT):
        self._length = length

    @linked
    def length(self):
        self._length = _TEST_LENGTH_A


class _TestSquare(object):
    """This is a test class for linked promises. I don't know what more you're expecting."""
    def __init__(self, width=None):
        if width is not None:
            self._side = _TestLine(width)

    @linked(chain=True)
    def side(self):
        self._side = _TestLine()

    @side.chain("length")
    def width(self):
        self._width = self.side.length

    @side.chain("length")
    def height(self):
        self._height = self.side.length

    @width.linked
    @height.linked
    def area(self):
        self._area = self.width * self.height


class _TestBox(object):
    """This is a test class for linked promises. I don't know what more you're expecting."""
    @linked(chain=True)
    def side(self):
        self._side = _TestLine()

    @linked(chain=True)
    def base(self):
        self._base = _TestSquare()

    @side.chain("length")
    @base.chain("area")
    def volume(self):
        self._volume = self.base.area * self.side.length


def _test_functionality():
    _test_object = _TestClass()
    _test = _test_object.test_attribute
    print(f"Test attribute value: {_test}")
    assert _test == _TEST_VALUE, "Test values did not match."
    _test_object.test_attribute = 5
    _test = _test_object.test_attribute
    assert _test == 5, "Set test values did not match."
    del _test_object.test_attribute
    assert not hasattr(_test_object, "_test_attribute"), "Test attribute did not get deleted."
    _should_be_4 = _test_object.test_member[2]
    assert _should_be_4 == 4, "Test member value did not match expected return."
    _should_be_16 = _test_object.test_member_from_method[2]
    assert _should_be_16 == 16, "Test member from method value did not match expected return."
    _test_object.test_member[2] = 2
    _should_be_2 = _test_object.test_member[2]
    assert _should_be_2 == 2, "Test member value did not change to set value."
    del _test_object.test_member[2]
    assert 2 not in _test_object.test_member, "Test member key was not deleted."


def _test_linkers():
    _test_object = _TestClassTwo()

    _test = _test_object.test_attribute
    print(f"Test attribute value: {_test}")
    assert _test == _TEST_VALUE, "Test values did not match."

    _test_link = _test_object.test_link
    print(f"Test link value: {_test_link}")
    assert _test_link == _TEST_VALUE, "Linked test values did not match."

    # Basic setting of linked link

    _test_linked_link = _test_object.test_linked_link
    print(f"Test linked link value: {_test_linked_link}")
    assert _test_linked_link == _TEST_VALUE, "Linked link test values did not match."

    _test_object.test_linked_link = _TEST_VALUE_TWO
    _test_linked_link = _test_object.test_linked_link
    print(f"Test linked link value: {_test_linked_link}")
    assert _test_linked_link == _TEST_VALUE_TWO, "Linked link new test values did not match."

    # Updating test_link attribute should also delete / reset test_linked_link attribute and test_attribute

    _test_object.test_link = _TEST_VALUE_TWO
    assert not hasattr(_test_object, '_test_linked_link'), "Test linked link not deleted after setting linked."
    _test_linked_link = _test_object.test_linked_link
    print(f"Test linked link value: {_test_linked_link}")
    assert _test_linked_link == _TEST_VALUE, "Reset linked link test values did not match."

    _test_link = _test_object.test_link
    print(f"New test link value: {_test_link}")
    assert _test_link == _TEST_VALUE_TWO, "New linked test values did not match."
    assert not hasattr(_test_object, '_test_attribute'), "Test attribute not deleted after setting linked."

    _test = _test_object.test_attribute
    print(f"New test attribute value: {_test}")
    assert _test == _TEST_VALUE_TWO, "New test values did not match."

    # Update test_linked_link attribute should not reset test_link as setter is explicit

    _test_object.test_linked_link = _TEST_VALUE_TWO
    assert hasattr(_test_object, '_test_link'), "Test linked deleted after setting linked link."
    assert hasattr(_test_object, '_test_attribute'), "Test attribute deleted after setting linked link."
    _test_linked_link = _test_object.test_linked_link
    assert _test_linked_link == _TEST_VALUE_TWO, "Linked link new test values did not match."

    # Deleting test_linked_link attribute should reset test_link and test_attribute as deleter is default and no init linkers

    del _test_object.test_linked_link
    assert not hasattr(_test_object, '_test_link'), "Test linked not deleted after deleting linked link."
    assert not hasattr(_test_object, '_test_attribute'), "Test attribute not deleted after deleting linked link."
    assert not hasattr(_test_object, '_test_linked_link'), "Test linked link not deleted after deleting linked link."
    _test_linked_link = _test_object.test_linked_link
    assert _test_linked_link == _TEST_VALUE, "Restored linked link test values did not match."

    _test_link = _test_object.test_link
    print(f"Restored test link value: {_test_link}")
    assert _test_link == _TEST_VALUE, "Restored linked test values did not match."

    _test = _test_object.test_attribute
    print(f"Restored test attribute value: {_test}")
    assert _test == _TEST_VALUE, "Restored test values did not match."

    # Deleting a property shouldn't cause an error if its dependent properties were not needed between deletions.

    del _test_object.test_link
    del _test_object.test_link


def _test_external_linkers():
    line = _TestLine()
    square = _TestSquare()
    box = _TestBox()

    # Values should be equal to defaults
    assert line.length == _TEST_LENGTH_INIT
    print(f"Default line length: {line.length}")
    assert square.area == _TEST_AREA_INIT
    print(f"Default square area: {square.area}")
    assert box.volume == _TEST_VOLUME_INIT
    print(f"Default box volume: {box.volume}")

    # Values should not change for unlinked objects despite linked classes
    line.length = _TEST_LENGTH_A
    assert line.length == _TEST_LENGTH_A
    assert square.area == _TEST_AREA_INIT
    assert box.volume == _TEST_VOLUME_INIT

    # Value of square should change as line's length keeper sets length to A
    del square.side.length
    assert square.area == _TEST_AREA_A
    # Unlinked box should remain the same.
    assert box.volume == _TEST_VOLUME_INIT

    # Volume of box should change if its base's sides' lengths are changed
    del box.base.side.length
    assert box.volume == _TEST_VOLUME_A_INIT_DEPTH

    # Volume of box should change if its side length is changed.
    del box.side.length
    assert box.volume == _TEST_VOLUME_A

    # Unlinked objects should remain the same.
    assert square.area == _TEST_AREA_A
    assert line.length == _TEST_LENGTH_A


def main():
    """Run tests to ensure everything still works."""
    _test_functionality()
    _test_linkers()
    _test_external_linkers()
    print("Tests passed!")


if __name__ == "__main__":
    main()
