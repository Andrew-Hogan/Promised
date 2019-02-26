"""Let's get excited about making some boilerplate properties!"""


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
    """This is a test class. I don't know what more you're expecting."""
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


def main():
    """Run tests to ensure everything still works."""
    _test_functionality()
    print("Tests passed!")


if __name__ == "__main__":
    main()
