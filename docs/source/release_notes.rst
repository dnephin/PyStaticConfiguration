
Release Notes
=============

v0.10.1
-------
* add ``compare_func`` support to ``MTimeComparator`` and adds ``build_compare_func`` helper
* fixes an error in ``_validate_iterable``

v0.10.0
-------
* add ``get_config_dict()`` to retrieve a mapping
* remove ``InodeComparator`` from the list of default comparators
* add ``PatchConfiguration`` for testing

v0.9.0
------
* support different file comparison strategies for the ConfigurationWatcher

v0.7.1
------
* bug fixes
* test failure fixes
* python3 support

v0.7.0
------
* `flatten` kwarg added to config loaders to disable dict flattening
  when the config is loaded
