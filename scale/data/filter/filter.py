"""Defines the class for filtering data"""
from __future__ import absolute_import
from __future__ import unicode_literals

from data.filter.exceptions import InvalidDataFilter


class DataFilter(object):
    """Represents a filter that either accepts or denies a set of data values
    """

    def __init__(self, accept):
        """Constructor

        :param accept: Whether this filter should accept or deny the data
        :type accept: bool
        """

        # TODO: take out accept param and do real implementation
        # TODO: there are a number of unit tests that will need to have real DataFilters created instead of
        # DataFilter(True) or DataFilter(False)
        self.accept = accept

        # TODO: after implementing this class, implement recipe.definition.node.ConditionNodeDefinition.__init__

    def is_data_accepted(self, data):
        """Indicates whether the given data passes the filter or not

        :param data: The data to check against the filter
        :type data: :class:`data.data.data.Data`
        :returns: True if the data is accepted, False if the data is denied
        :rtype: bool
        """

        # TODO: provide real implementation
        return self.accept

    def is_filter_equal(self, data_filter):
        """Indicates whether the given data filter is equal to this filter or not

        :param data_filter: The data filter
        :type data_filter: :class:`data.filter.filter.DataFilter`
        :returns: True if the data filter is equal to this one, False otherwise
        :rtype: bool
        """

        # TODO: provide real implementation
        return self.accept == data_filter.accept

    def validate(self, interface):
        """Validates this data filter against the given interface

        :param interface: The interface describing the data that will be passed to the filter
        :type interface: :class:`data.interface.interface.Interface`
        :returns: A list of warnings discovered during validation
        :rtype: list

        :raises :class:`data.filter.exceptions.InvalidDataFilter`: If the data filter is invalid
        """

        warnings = []

        # TODO: implement

        return warnings
