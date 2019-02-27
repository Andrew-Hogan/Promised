# Promised

### promise

A flexible delayed-evaluation cached property with get/set/del/init capabilities for inter-property relationships.

### linked

A dependency-managing promise which will refresh dependent properties when any of its linker methods are called. (typically, deleter and setter)

### Member

A cached-mapping extension class designed for the @promise decorator, similar to explicitly (im-)mutable memoization.

## Get

Type this into terminal / command-line:
```
pip install promised
```

And this into Python:
```
from promised import promise, linked, Member  # linked are dependent promises, Member is for cached-mapping extension.
```

## Purpose

Why? Because I found myself doing this too often:
```
@property
def property_public_name(self):
    '''Why am I typing the same lines with tiny changes in every project all the time?'''
    try:
        return self._property_public_name_with_leading_underscore
    except AttributeError:
        self._property_public_name_with_leading_underscore = self._method_to_calculate_property()
    return self._property_public_name_with_leading_underscore
```

## Usage

Now, it looks like this:
```
@promise
def property_public_name(self):
    '''Now this is promising!'''
    self._property_public_name_with_leading_underscore = self._method_to_calculate_property()
```

It's still accessed like this:
```
property_value = self.property_public_name
```

And you can still do this:
```
@property_public_name.setter
@property_public_name.deleter
@property_public_name.getter
```

You can group a bunch of promises up with the same keeper by passing in the name of the private variable (the variable initially set in the promise's keeper) to the promise's \_\_init\_\_:
```
def _set_associated_properties(self):
    associated_map_one = {}
    associated_map_two = {}
    for thing in self.iterable:
        associated_map_one = thing.map_one(associated_map_one)
        associated_map_two = thing.map_two(associated_map_two)
    self._property_one_public_name = associated_map_one
    self._property_two_public_name = associated_map_two

property_one_public_name = promised(_set_associated_properties, name="_property_one_public_name")
property_two_public_name = promised(_set_associated_properties, name="_property_two_public_name")
```
You can link dependent attributes together using an @linked property (which functions similarly to a promised property) and decorating any of the dependent properties' getter / setter / deleter / keeper methods with the @linked_property_name.linked decorator a single time per dependent property:
```
@linked
def heroes(self):
    self._heroes = None

@heroes.linked
@promise
def future_of_townsville(self):
    self._future_of_townsville = "Bleak" if not self.heroes else "FAN-tastic!"

@future_of_townsville.deleter
def future_of_townsville(self):
    del self._future_of_townsville

@heroes.linker
@heroes.setter
def heroes(self, value):
    self._heroes = value

def test_town_turnaround(self):
    ""Setting self.heroes to a different value should reset its dependent properties."""
    assert not hasattr(self, "_heroes"), "promise should not have already been kept!"
    assert not hasattr(self, "_future_of_townsville"), "promise should not have already been kept!"
    assert self.future_of_townsville == "Bleak", "There should be no heroes - yet!"
    assert self.heroes is None, "There should be no heroes - yet!"
    self.heroes = "POWER-PUFF GIRLS"
    assert not hasattr(self, "_future_of_townsville"), "The future of townsville is dependent on heroes, so it should be deleted once changed!"
    assert self.future_of_townsville == "FAN-tastic!", "The future of townsville should be looking up!"
```

@linked properties will automatically refresh dependent properties when a @linker method of theirs is called. For ease of use, as this will require at least a deletion method in dependent properties, @linked properties are @promise properties with default deleters and setters which are also default linkers. Using defaults on linked properties, the previous example becomes:
```
@linked
def heroes(self):
    self._heroes = None

@heroes.linked
@linked
def future_of_townsville(self):
    self._future_of_townsville = "Bleak" if not self.heroes else "FAN-tastic!"

def test_town_turnaround(self):
    ""Setting self.heroes to a different value should reset its dependent properties."""
    ...
```

See documentation in boiler_property.py for further details on removing default deleters / setters / linkers:
```
@linked(linkers=("keeper",)
def property_which_refreshes_dependent_properties_when_keeper_method_used(self):
    """This would typically reset all dependent properties after this property is accessed for the first time and first access post-refresh/deletion."""
    self._property_which_refreshes_dependent_properties_when_keeper_method_used = "RESET"

@linked(deleter=False, setter=False, linkers=("getter",)
def read_only_property_which_refreshes_dependent_properties_on_every_access(self):
    """Not advised for properties which access this property once reset (as the typical dependent property would.)"""
    self._read_only_property_which_refreshes_dependent_properties_on_every_access = None
```

You can use the Member class to create a cached promised property which varies on input (like memoization, but explicitly mutable / not-mutable):
```
def _children_of_parent_with_attribute_value(self, parent, child_attribute_value):
    return self.parent_children_map[parent] & self.attribute_value_to_set_of_objects_map[child_attribute_value]

@promise
def adult_children(self):
    self._adult_children = Member(self._children_of_parent_with_attribute_value, "The White House")
```

Which is then accessed like this:
```
donnie = countries.adult_children["America"]
```

## Future

These are just the first steps in patterns I've recognized as useful for explicit cached properties, and I'm very interested in building in more automated support for associated & dependent properties - please feel free to share any suggestions.

## Copyright

promised module by Andrew M. Hogan. (promised &copy; 2019 Hogan Consulting Group)

## License

Licensed under the Apache License.
