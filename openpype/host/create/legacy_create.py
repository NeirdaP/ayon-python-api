"""Create workflow moved from avalon-core repository.

Renamed classes and functions
- 'Creator' -> 'LegacyCreator'
- 'create'  -> 'legacy_create'
"""

import logging
import collections

from openpype.host.process_tools import registered_host
from .lib import get_subset_name


class LegacyCreator(object):
    """Determine how assets are created"""
    label = None
    family = None
    defaults = None
    maintain_selection = True

    dynamic_subset_keys = []

    log = logging.getLogger("LegacyCreator")
    log.propagate = True

    def __init__(self, name, asset, options=None, data=None):
        self.name = name  # For backwards compatibility
        self.options = options

        # Default data
        self.data = collections.OrderedDict()
        self.data["id"] = "pyblish.avalon.instance"
        self.data["family"] = self.family
        self.data["asset"] = asset
        self.data["subset"] = name
        self.data["active"] = True

        self.data.update(data or {})

    def process(self):
        pass

    @classmethod
    def get_dynamic_data(
        cls, variant, task_name, asset_id, project_name, host_name
    ):
        """Return dynamic data for current Creator plugin.

        By default return keys from `dynamic_subset_keys` attribute as mapping
        to keep formatted template unchanged.

        ```
        dynamic_subset_keys = ["my_key"]
        ---
        output = {
            "my_key": "{my_key}"
        }
        ```

        Dynamic keys may override default Creator keys (family, task, asset,
        ...) but do it wisely if you need.

        All of keys will be converted into 3 variants unchanged, capitalized
        and all upper letters. Because of that are all keys lowered.

        This method can be modified to prefill some values just keep in mind it
        is class method.

        Returns:
            dict: Fill data for subset name template.
        """
        dynamic_data = {}
        for key in cls.dynamic_subset_keys:
            key = key.lower()
            dynamic_data[key] = "{" + key + "}"
        return dynamic_data

    @classmethod
    def get_subset_name(
        cls, variant, task_name, folder_id, project_name, host_name
    ):
        """Return subset name created with entered arguments.

        Logic extracted from Creator tool. This method should give ability
        to get subset name without the tool.

        TODO: Maybe change `variant` variable.

        By default is output concatenated family with user text.

        Args:
            variant (str): What is entered by user in creator tool.
            task_name (str): Context's task name.
            folder_id (ObjectId): Id of context's folder.
            project_name (str): Context's project name.
            host_name (str): Name of host.

        Returns:
            str: Formatted subset name with entered arguments. Should match
                config's logic.
        """

        dynamic_data = cls.get_dynamic_data(
            variant, task_name, folder_id, project_name, host_name
        )

        return get_subset_name(
            cls.family,
            variant,
            task_name,
            folder_id,
            project_name,
            host_name,
            dynamic_data=dynamic_data
        )


# This should be probably moved as method to HostImplementation?
def legacy_create(Creator, name, folder_name, options=None, data=None):
    """Create a new instance

    Associate nodes with a subset and family. These nodes are later
    validated, according to their `family`, and integrated into the
    shared environment, relative their `subset`.

    Data relative each family, along with default data, are imprinted
    into the resulting objectSet. This data is later used by extractors
    and finally folder browsers to help identify the origin of the folder.

    Arguments:
        Creator (Creator): Class of creator
        name (str): Name of subset
        folder_name (str): Name of folder_name
        options (dict, optional): Additional options from GUI
        data (dict, optional): Additional data from GUI

    Raises:
        NameError: If `subset` already exists
        KeyError: If dynamic property is invalid
        RuntimeError: On host error

    Returns:
        dict: Created instance.
    """

    host = registered_host()
    plugin = Creator(name, folder_name, options, data)

    if plugin.maintain_selection is True:
        with host.maintained_selection():
            print("Running %s with maintained selection" % plugin)
            instance = plugin.process()
        return instance

    print("Running %s" % plugin)
    instance = plugin.process()
    return instance