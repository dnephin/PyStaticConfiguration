
.PHONY: clean docs test


clean:
	find -name *.pyc -exec rm {} \;
	rm -r docs/build/html


docs:
	sphinx-build -b html docs/source/ docs/build/html


test:
	testify tests
