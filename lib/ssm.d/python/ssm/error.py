#! /usr/bin/env python
#
# error.py

"""Provides Error class.
"""

class Error:
	"""Used to indicates an error and provide a message.
	"""

	def __init__(self, msg):
		self.msg = msg

	def __repr__(self):
		return "%s" % str(self.msg)