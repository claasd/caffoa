rmdir /s /q dist
rmdir /s /q build
rmdir /s /q caffoa.egg-info
pause
python setup.py sdist bdist_wheel
python -m twine upload dist/*