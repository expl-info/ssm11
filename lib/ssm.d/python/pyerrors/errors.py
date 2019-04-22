#! /usr/bin/env python2
#
# pyerrors/errors.py

# see: https://opensource.org/licenses/BSD-3-Clause
#
# Copyright (c) 2019 John Marshall
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
Provides an alternative to minimally differentiated integer exit
codes and exceptions.
"""

import sys

class Error:
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return str(self.msg)

    def __repr__(self):
        return """<Error msg="%s">""" % str(self.msg)

def __perror(erro):
    sys.stderr.write("%s\n" % str(erro))

def is_error(erro):
    return isinstance(erro, Error)

def onerror_exit(erro, exitcode=1):
    if is_error(erro):
        sys.exit(exitcode)

def onerror_raise(erro, exccls=Exception):
    if is_error(erro):
        raise exccls(str(erro))

def perror(erro):
    if is_error(erro):
        __perror(erro)

def perror_exit(erro, exitcode=1):
    """On Error, write string to stderr. Exit on non-zero exitcode.
    """
    if is_error(erro):
        __perror(erro)
        if exitvalue != 0:
            sys.exit(exitcode)

def perror_raise(erro, exccls=Exception):
    """On Error, write string to stderr. Raise exception on non-None exccls.
    """
    if is_error(erro):
        __perror(erro)
        if exccls != None:
            raise exccls(str(erro))
