=====
Usage
=====

Kylie's design is based on Django's ORM, so it may look pretty familiar. To use
Kylie Models in a project, first import it. The API is pretty small::

    from kylie import Model, Attribute, Relation

The simplest use is to extend ``Model``, and attach some ``Attribute``
instances::

    class Animal(Model):
        id = Attribute()
        name = Attribute()

If you have a dictionary of JSON types, you can deserialize it into an `Animal`
instance as follows::

    daisy_pig = Animal.deserialize({
        'id': 1234,
        'name': 'Daisy',
    })

This will give you an object with a bunch of attributes you can query, such as
``daisy_pig.id`` and ``daisy_pig.name``.

We can do the opposite, by calling serialize on an instantiated ``Animal``
instance::

    >>> daisy_data = daisy_pig.serialize()
    >>> daisy_data
    {
        'id': 1234,
        'name': 'Daisy',
    }

Instantiating a ``Model`` with a bunch of data can be done with
keyword params::

    daisy_pig = Animal(animal_id=1234, name='Daisy')

You can then call ``serialize`` on this to return a dict containing the
object's data.

*But that's not very interesting*, so let's see what else we can do.

.. _name mapping:

Name Mapping
------------

``id`` is not a very good attribute name in Python. So we probably want to map
the JSON attribute's key to something like ``animal_id``, so let's try that::

    class Animal(Model):
        animal_id = Attribute('id')
        name = Attribute()

Now if we run the ``deserialize`` call above, then ``daisy_pig`` will have an
attribute called ``animal_id`` instead of ``id``. Result!

This is particularly nice if you're mapping a bunch of keys that use
*javaNamingConvention* to *python_naming_convention*.

Type Mapping
------------

So we can do name-mapping, but what about type-mapping? For example, JSON
doesn't support timestamps unless they're stored as numbers or formatted
strings, but that's not very nice in Python, where we have (slightly) nicer
``datetime`` objects.

Can Kylie do the mapping for you? You bet! You'll need a function that converts
from the serialized form to the Python type, and another that does the reverse
mapping though. Let's define those::

    from datetime import datetime, timedelta

    def dt_to_milliseconds(dt):
        epoch = datetime.utcfromtimestamp(0)
        delta = dt - epoch
        return int(delta.total_seconds() * 1000.0)

    def milliseconds_to_dt(millis):
        epoch = datetime.utcfromtimestamp(0)
        return epoch + timedelta(seconds=millis / 1000.0)

And now we create an ``Attribute`` using the ``python_type`` and
``serialized_type`` parameters::

    class Animal(Model):
        animal_id = Attribute('id')
        name = Attribute()
        birth_date = Attribute(python_type=milliseconds_to_dt,
                               serialized_type=dt_to_milliseconds)


Now you can do the following::

    >>> daisy_pig = Animal.deserialize({
    ...     'id': 1234, 'name': 'Daisy', 'birth_date': 1428870071656
    ... })
    >>> daisy_pig.birth_date
    datetime.datetime(2015, 4, 12, 20, 21, 11, 656000)



.. _nested models:

Nested Models
-------------

If a person drives a car, you can define the following::

    class Car(Model):
        color = Attribute()

    class Person(Model):
        name = Attribute()
        car = Relation(Car)

The following will now work::

    >>> maggie = Person.deserialize({
    ...     'name': 'Margaret',
    ...     'car': {
    ...         'color': 'red'
    ...     }
    ... })

    >>> maggie.car
    <__main__.Car instance as #123455>

    >>> maggie.car.color
    'red'


Nested Sequences
----------------

If a car has multiple wheels, you can store them in an embedded sequence::

    class Wheel(Model):
        front = Attribute()
        side = Attribute()

    class Car(Model):
        wheels = Relation(Wheel, sequence=True)

Now you can store and lists of Wheels with your car::

    >>> reliant_robin = Car.deserialize({
    ...     'wheels': [
    ...         dict(front=True, side='Middle'),
    ...         dict(front=False, side='Left'),
    ...         dict(front=False, side='Right'),
    ...     ]
    ... })

    >>> reliant_robin.wheels
    [<__main__.Wheel at 0x10306bdd0>,
     <__main__.Wheel at 0x10306ba50>,
     <__main__.Wheel at 0x10306bb90>]


What else should I know?
------------------------

If a value in the input dict is ``None``, it will be set to ``None`` in the
deserialized object. There's no way to ensure a value is non-None.

If an attribute is missing from the input dict, ``deserialize`` will fail with
an exception. There is currently no way to flag an attribute as 'possibly
missing'. It's on the list.

Currently, Kylie doesn't do any validation of anything. If you get an exception
that seems like a bad fit, please raise an issue on GitHub.

