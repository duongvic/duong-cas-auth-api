import abc
import ast
import csv
import json
import re
import sys

import six
from six.moves import configparser
import xmltodict
import yaml

from oslo_serialization import base64


@six.add_metaclass(abc.ABCMeta)
class StreamCodec(object):

    @abc.abstractmethod
    def serialize(self, data):
        """Serialize a Python object into a stream.
        """

    @abc.abstractmethod
    def deserialize(self, stream):
        """Deserialize stream data into a Python structure.
        """


class Base64Codec(StreamCodec):
    """Serialize (encode) and deserialize (decode) using the base64 codec.
    To read binary data from a file and b64encode it, used the decode=False
    flag on operating_system's read calls.  Use encode=False to decode
    binary data before writing to a file as well.
    """

    # NOTE(zhaochao): migrate to oslo_serialization.base64 to serialize(return
    # a text object) and deserialize(return a bytes object) data.

    def serialize(self, data):
        return base64.encode_as_text(data)

    def deserialize(self, stream):
        return base64.decode_as_bytes(stream)
