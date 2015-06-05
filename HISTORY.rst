.. :changelog:

=======
History
=======

0.3.0 (2015-06-05)
------------------

* MappedModelChoice & BaseModelChoice for determining Model to deserialize
  at runtime.
* Change to internal Attribute interface (will lead to minor version bump)

  ``_apply_model`` has been replaced with a direct set of ``attr_name``.

* Minor code quality improvements.
* Documentation improvements.


0.2.0 (2015-04-22)
------------------

* Added list support to Relation with ``sequence=True`` parameter.

0.1.1 (2015-04-12)
------------------

* Removed print statement inside class constructor.


0.1.0 (2015-04-12)
------------------

* First release on PyPI.
