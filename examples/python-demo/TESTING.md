# Testing

Run the complete test suite with:

```sh
python3 -m unittest discover -s . -p 'test_*.py'
```

Behavior changes require focused assertions. Bug fixes require a regression
test. The suite uses Python's standard-library `unittest` runner.
