"""Defines the class that represents a job configuration"""
from __future__ import unicode_literals

from job.configuration.exceptions import InvalidJobConfiguration


DEFAULT_PRIORITY = 100


class JobConfiguration(object):
    """Represents the configuration for running a job"""

    def __init__(self):
        """Constructor
        """

        # Jobs can be configured to have a main (default) workspace for all output files, as well as have a specific
        # workspace for each output name
        self.main_output_workspace = None
        self.output_workspaces = {}  # {Output name: Workspace name}

        self.priority = DEFAULT_PRIORITY

        self.mounts = {}  # {Name: MountConfig}
        self.settings = {}  # {Name: Value}

    def add_mount(self, mount_config):
        """Adds the given mount configuration

        :param mount_config: The mount configuration to add
        :type mount_config: :class:`job.configuration.mount.MountConfig`

        :raises :class:`job.configuration.exceptions.InvalidJobConfiguration`: If the mount is a duplicate
        """

        if mount_config.name in self.mounts:
            raise InvalidJobConfiguration('Duplicate mount \'%s\'' % mount_config.name)

        self.mounts[mount_config.name] = mount_config

    def add_setting(self, setting_name, setting_value):
        """Adds the given setting value

        :param setting_name: The setting name
        :type setting_name: string
        :param setting_value: The setting value
        :type setting_value: string

        :raises :class:`job.configuration.exceptions.InvalidJobConfiguration`: If the setting is a duplicate or invalid
        """

        if setting_name in self.settings:
            raise InvalidJobConfiguration('Duplicate setting \'%s\'' % setting_name)
        if not setting_value:
            raise InvalidJobConfiguration('The value for setting \'%s\' must be a non-empty string' % setting_name)

        self.settings[setting_name] = setting_value

    # TODO: implement validating against a Seed manifest
    def validate(self, interface):
        """Validates the configuration against the given Seed manifest

        :param interface: The interface dict for the job type
        :type interface: dict
        :returns: A list of warnings discovered during validation
        :rtype: list

        :raises :class:`job.configuration.exceptions.InvalidJobConfiguration`: If the configuration is invalid
        """

        warnings = []

        for mount_config in self.mounts.values():
            warnings.extend(mount_config.validate())

        # TODO: ensure output workspaces are valid
        # TODO: do warnings for ignored mounts and settings not defined in Seed
        # TODO: do warnings for mounts, settings, and output workspaces in Seed, but not defined here
        # TODO: strip out secret settings? how does this work now?

        return warnings
