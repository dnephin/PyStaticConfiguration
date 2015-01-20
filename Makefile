
.PHONY: clean docs test upload


clean:
	find -name *.pyc -exec rm {} \;
	rm -rf docs/build/html
	rm -rf __pycache__


docs:
	sphinx-build -b html docs/source/ docs/build/html


test:
	tox -e py26


upload:
	python setup.py sdist upload upload_docs
