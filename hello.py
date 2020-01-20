import pytest
import os
from os.path import isfile, join

TEST_DIR = os.path.dirname(os.path.realpath(__file__))
FIXTURE_DIR = os.path.join(TEST_DIR, 'request_files')
FIXTURE_FILES = [
	os.path.join(FIXTURE_DIR, name) 
	for name in os.listdir(FIXTURE_DIR) if isfile(join(FIXTURE_DIR, name))
]

print(FIXTURE_FILES)
