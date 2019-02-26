# Promised
###promise
A flexible delayed-evaluation cached property with get/set/del/init capabilities for inter-property relationships.

###Member

A cached-mapping extension class designed for the @promise wrapper, similar to explicitly (im-)mutable memoization.

##Get

Type this into terminal / command-line:

    pip install promised

And this into Python:

    from promised import promise, Member  # Member is for cached-mapping extension.

##Purpose

Why? Because I found myself doing this too often:

    @property
    def property_public_name(self):
        '''Why am I typing the same lines with tiny changes in every project all the time?'''
        try:
            return self._property_public_name_with_leading_underscore
        except AttributeError:
            self._property_public_name_with_leading_underscore = self._method_to_calculate_property()
        return self._property_public_name_with_leading_underscore

##Usage

Now, it looks like this:

    @promise
    def property_public_name(self):
        '''Now this is promising!'''
        self._property_public_name_with_leading_underscore = self._method_to_calculate_property()

It's still accessed like this:

    property_value = self.property_public_name

And you can still do this:

    @property_public_name.setter
    @property_public_name.deleter
    @property_public_name.getter

You can group a bunch of promises up with the same keeper by passing in the name of the private variable (the variable initially set in the promise's keeper) to the promise's \_\_init\_\_:

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

And you can use the Member class to create a cached promised property which varies on input (like memoization, but explicitly mutable / not-mutable):

    def _children_of_parent_with_attribute_value(self, parent, child_attribute_value):
        return self.parent_children_map[parent] & self.attribute_value_to_set_of_objects_map[child_attribute_value]
    
    @promise
    def adult_children(self):
        self._adult_children = Member(self._children_of_parent_with_attribute_value, "The White House")
    
Which is then accessed like this:

    donnie = countries.adult_children["America"]

##Future

These are just the first steps in patterns I've recognized as useful for explicit cached properties, and I'm very interested in building in more automated support for associated & dependent properties - please feel free to share any suggestions.

##Copyright

promised module by Andrew M. Hogan. (promised &copy; 2019 Hogan Consulting Group)

##License

Licensed under the Apache License
