
import promised.boiler_property


_TEST_VALUE = "Set by promise keeper"
_TEST_VALUE_TWO = "Set by linked update"
_TEST_LENGTH_INIT = 2
_TEST_LENGTH_A = 5
_TEST_AREA_INIT = _TEST_LENGTH_INIT ** 2
_TEST_VOLUME_INIT = _TEST_AREA_INIT * _TEST_LENGTH_INIT
_TEST_AREA_A = _TEST_LENGTH_A ** 2
_TEST_VOLUME_A_INIT_DEPTH = _TEST_AREA_A * _TEST_LENGTH_INIT
_TEST_VOLUME_A = _TEST_AREA_A * _TEST_LENGTH_A


class _TestClass(object):
    """This is a test class for promises & Members. I don't know what more you're expecting."""
    @promised.boiler_property.promise
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

    @promised.boiler_property.promise
    def test_member(self):
        assert self.__class__ is _TestClass, "Keeper method for member not bound to instance of _TestClass."
        self._test_member = promised.boiler_property.Member(lambda x: x * x)

    def _calc_test_member(self, key):
        assert self.__class__ is _TestClass, "Getter method for method member not bound to instance of _TestClass."
        return self.test_member[self.test_member[key]]

    @promised.boiler_property.promise
    def test_member_from_method(self):
        assert self.__class__ is _TestClass, "Keeper method for method member not bound to instance of _TestClass."
        self._test_member_from_method = promised.boiler_property.Member(self._calc_test_member)

    def __repr__(self, *_, **__):
        return f"<{self.__class__.__name__} object {id(self)}>"

    __str__ = __repr__


class _TestClassTwo(object):
    """This is a test class for linked promises. I don't know what more you're expecting."""
    @promised.boiler_property.linked
    def test_linked_link(self):
        assert self.__class__ is _TestClassTwo, "Linked link keeper method not bound to instance of _TestClassTwo."
        assert not hasattr(self, "_test_linked_link"), ("Linked link keeper method called "
                                                        "despite existing self._test_linked_link.")
        self._test_linked_link = _TEST_VALUE
        assert self._test_linked_link == _TEST_VALUE, ("self._test_linked_link not set to _TEST_VALUE "
                                                       "in linked link keeper.")

    @test_linked_link.linked
    @promised.boiler_property.linked
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

    @promised.boiler_property.promise
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


class _TestLine(object):
    """This is a test class for linked promises. I don't know what more you're expecting."""
    def __init__(self, length=_TEST_LENGTH_INIT):
        self._length = length

    @promised.boiler_property.linked
    def length(self):
        self._length = _TEST_LENGTH_A


class _TestSquare(object):
    """This is a test class for linked promises. I don't know what more you're expecting."""
    def __init__(self, width=None):
        if width is not None:
            self._side = _TestLine(width)

    @promised.boiler_property.linked(chain=True)
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
    @promised.boiler_property.linked(chain=True)
    def side(self):
        self._side = _TestLine()

    @promised.boiler_property.linked(chain=True)
    def base(self):
        self._base = _TestSquare()

    @side.chain("length")
    @base.chain("area")
    def volume(self):
        self._volume = self.base.area * self.side.length


def test_functionality():
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


def test_linkers():
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


def test_external_linkers():
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
    test_functionality()
    test_linkers()
    test_external_linkers()
    print("Tests passed!")


if __name__ == "__main__":
    main()
