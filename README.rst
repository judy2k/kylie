=====
Kylie
=====

.. image:: https://img.shields.io/travis/judy2k/kylie.svg
        :target: https://travis-ci.org/judy2k/kylie

.. image:: https://coveralls.io/repos/judy2k/kylie/badge.svg?branch=master
        :target: https://coveralls.io/r/judy2k/kylie?branch=master

.. image:: https://landscape.io/github/judy2k/kylie/master/landscape.svg?style=flat
        :target: https://landscape.io/github/judy2k/kylie/master
        :alt: Code Health

.. image:: https://img.shields.io/pypi/v/kylie.svg
        :target: https://pypi.python.org/pypi/kylie


Kylie provides mappings between JSON data structures and Python objects. It
provides a reasonable amount of power with only a tiny bit of magic, and it has
100% code coverage.

Features
--------

* Free software: BSD license
* Documentation: https://kylie.readthedocs.org/
* Allows `name mapping`_ between Models and python dictionary keys.
* Allows `type conversion`_ when serializing and de-serializing objects.
* Automatic serialization/deserialization of `nested models`_.
* Not bound to JSON in any way, and should also be useful for MessagePack_
* Supports Python 2.6+ & 3.3+

Example
-------

.. code-block:: python

    class SpanishInquisitionModel(Model):
        inquisition_id = Attribute('id')
        expected = Attribute(python_type=bool, serialized_type=int)

Then:

.. code-block:: python

    >>> surprise = SpanishInquisitionModel(inquisition_id=1234, expected=False)
    >>> surprise.inquisition_id
    1234
    >>> surprise.serialize()
    {'id': 1234, expected=0}

Note that the attribute ``inquisition_id`` becomes the dict key ``"id"``, and
expected is mapped to ``0`` instead of ``False``.

We can now take this dict, ``dumps`` it to JSON, and somewhere else call
the following on the json_data (which is a dict returned from ``loads``):

.. code-block:: python

    >>> my_surprise = SpanishInquisitionModel.deserialize(json_data)
    >>> my_surprise.inquisition_id
    1234
    >>> my_surprise.expected
    False

Kylie supports `nested models`_, so you can embed
other Model instances inside the data, and Kylie will manage serialization and
deserialization of them for you.


Non-Features
------------

So what doesn't Kylie do yet? Well, there are a few things, because it's
very new:

* Doesn't have any mechanism for validation. I plan to add this once I
  decide the best way to do it. *Ideas welcome!*
* Doesn't have any built-in mechanism for choosing between different types to
  deserialize a dict to. This can be done through customized type mapper
  functions. At the very least, I'll document this soon. I plan to add the
  ability to automatically deserialize to a type based on, for example, a
  ``__type__`` item in the dict.
* No post-serialize or post-deserialize options, unless you do it yourself.
  This would allow wiring up of objects that are referred to by ``id`` and
  provided elsewhere in the serialized data-structure, for example.

So, lots to do, but I think Kylie is already useful.


Why is it called Kylie?
-----------------------

Back in the late 80's (I'm old!) Kylie and Jason were today's Kim and Kanye.
**This** Kylie works well with JSON. Geddit?

.. image:: http://upload.wikimedia.org/wikipedia/en/1/1a/KylieEspeciallyForYouCover.png

.. _nested models: http://kylie.readthedocs.org/en/latest/usage.html#nested-models
.. _type conversion: http://kylie.readthedocs.org/en/latest/usage.html#type-mapping
.. _name mapping: http://kylie.readthedocs.org/en/latest/usage.html#name-mapping
.. _MessagePack: http://msgpack.org/
