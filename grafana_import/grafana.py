import os
import re
import traceback
import typing as t
import unicodedata

import grafana_client.api as GrafanaApi
import grafana_client.client as GrafanaClient

from grafana_import.constants import PKG_NAME


class GrafanaDashboardNotFoundError(Exception):
    """
    input:
       dashboard_name
       folder
       message

    """

    def __init__(self, dashboard_name, folder, message):
        self.dashboard = dashboard_name
        self.folder = folder
        self.message = message
        # Backwards compatible with implementations that rely on just the message.
        super(GrafanaDashboardNotFoundError, self).__init__(message)


class GrafanaFolderNotFoundError(Exception):
    """
    input:
       folder
       message

    """

    def __init__(self, folder, message):
        self.folder = folder
        self.message = message
        # Backwards compatible with implementations that rely on just the message.
        super(GrafanaFolderNotFoundError, self).__init__(message)


def remove_accents_and_space(input_str: str) -> str:
    """
    build a valid file name from dashboard name.

    as mentioned in the function name remove ....

    input: a dashboard name

    :result: converted string
    """
    nfkd_form = unicodedata.normalize("NFKD", input_str)
    res = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    return re.sub(r"\s+", "_", res)


class Grafana:
    # * to store the folders list, dashboards list (kind of cache)
    folders: t.List[t.Any] = []
    dashboards: t.List[t.Any] = []

    def __init__(self, **kwargs):

        # Configure Grafana connectivity.
        if "url" in kwargs:
            self.grafana_api = GrafanaApi.GrafanaApi.from_url(
                url=kwargs["url"], credential=kwargs.get("credential", os.environ.get("GRAFANA_TOKEN"))
            )
        else:
            config = {}
            config["protocol"] = kwargs.get("protocol", "http")
            config["host"] = kwargs.get("host", "localhost")
            config["port"] = kwargs.get("port", 3000)
            config["token"] = kwargs.get("token", None)
            config["verify_ssl"] = kwargs.get("verify_ssl", True)

            self.grafana_api = GrafanaApi.GrafanaApi(
                auth=config["token"],
                host=config["host"],
                protocol=config["protocol"],
                port=config["port"],
                verify=config["verify_ssl"],
            )

        self.search_api_limit = kwargs.get("search_api_limit", 5000)
        # * set the default destination folder for dash
        self.grafana_folder = kwargs.get("folder", "General")

        # * when importing dash, allow to overwrite dash if it already exists
        self.overwrite = kwargs.get("overwrite", True)

        # * when importing dash, if dashboard name exists, but destination folder mismatch
        # * allow to create new dashboard with same name in specified folder.
        self.allow_new = kwargs.get("allow_new", False)

        # * when importing dash, keep dashboard uid defined in the json file.
        self.keep_uid = kwargs.get("keep_uid", False)

        # * try to connect to the API
        try:
            res = self.grafana_api.health.check()
            if res["database"] != "ok":
                raise Exception("grafana is not UP")
        except:
            raise

    def find_dashboard(self, dashboard_name: str) -> t.Union[t.Dict[str, t.Any], None]:
        """
        Retrieve dashboards which name are matching the lookup named.
        Some api version didn't return folderTitle. Requires to lookup in two phases.
        """

        # Init cache for dashboards.
        if len(Grafana.dashboards) == 0:
            # Collect all dashboard names.
            try:
                res = self.grafana_api.search.search_dashboards(type_="dash-db", limit=self.search_api_limit)
            except Exception as ex:
                raise Exception("error: {}".format(traceback.format_exc())) from ex
            Grafana.dashboards = res

        dashboards = Grafana.dashboards

        folder = {
            "id": 0,
            "title": "General",
        }
        if not re.match("general", self.grafana_folder, re.IGNORECASE):
            found_folder = self.get_folder(folder_name=self.grafana_folder)
            if found_folder is not None:
                folder = found_folder

        board = None
        # * find the board uid in the list
        for cur_dash in dashboards:
            if cur_dash["title"] == dashboard_name:
                # set current dashbard as found candidate
                board = cur_dash
                # check the folder part
                if ("folderTitle" in cur_dash and cur_dash["folderTitle"] == folder["title"]) or (
                    "folderTitle" not in cur_dash and folder["id"] == 0
                ):
                    # this is a requested folder or no folder !
                    break

        return board

    def export_dashboard(self, dashboard_name: str) -> t.Dict[str, t.Any]:
        """
        retrive the dashboard object from Grafana server.
           params:
              dashboard_name (str): name of the dashboard to retrieve
           result:
              dashboard (dict [json])
        """

        try:
            board = self.find_dashboard(dashboard_name)

            if board is None:
                raise GrafanaClient.GrafanaClientError(response=None, message="Not Found", status_code=404)

            # Fetch the dashboard JSON representation by UID.
            return self.grafana_api.dashboard.get_dashboard(board["uid"])
        except Exception as ex:
            if isinstance(ex, GrafanaClient.GrafanaClientError) and ex.status_code == 404:
                raise GrafanaDashboardNotFoundError(
                    dashboard_name, self.grafana_folder, f"Dashboard not found: {dashboard_name}"
                ) from ex
            raise

    def remove_dashboard(self, dashboard_name: str) -> t.Dict[str, t.Any]:
        """
        Retrieve the dashboard object from Grafana server and remove it.
           params:
              dashboard_name (str): name of the dashboard to retrieve
           result:
              True or Exception
        """

        res = {}
        folder = {
            "id": 0,
            "title": self.grafana_folder,
        }

        # Check if the destination folder is `General`.
        if not re.match("general", self.grafana_folder, re.IGNORECASE):
            # ** check 'custom' folder existence (custom != General)
            folder = self.get_folder(self.grafana_folder)
            if folder is None:
                raise GrafanaFolderNotFoundError(
                    self.grafana_folder,
                    f"Folder not found: {self.grafana_folder}",
                )

        # Collect the board object itself from it uid.
        board = self.find_dashboard(dashboard_name)

        if board is None:
            raise GrafanaDashboardNotFoundError(dashboard_name, folder["title"], "dashboard not found")

        if (folder["id"] == 0 and "folderId" in board and board["folderId"] != folder["id"]) or (
            folder["id"] != 0 and "folderId" not in board
        ):
            raise GrafanaApi.GrafanaBadInputError(
                "Dashboard name found but in folder '{0}'!".format(board["folderTitle"])
            )

        if "uid" in board:
            res = self.grafana_api.dashboard.delete_dashboard(board["uid"])

        return res

    def get_folder(self, folder_name: str = None, folder_uid: str = None):
        """
        try to find folder meta data (uid...) from folder name
           params:
              folder_name (str): name of the folder (case sensitive) into Grafana folders tree
           return:
              folder object (dict)
        """
        if folder_name is None and folder_uid is None:
            return None

        # * init cache for folders.
        if len(Grafana.folders) == 0:
            res = self.grafana_api.folder.get_all_folders()
            Grafana.folders = res

        folders = Grafana.folders
        folder = None

        for tmp_folder in folders:

            if (folder_name is not None and folder_name == tmp_folder["title"]) or (
                folder_uid is not None and folder_uid == tmp_folder["folderId"]
            ):
                folder = tmp_folder
                break

        return folder

    def import_dashboard(self, dashboard: t.Dict[str, t.Any]) -> bool:

        # ** build a temporary meta dashboard struct to store info
        # ** by default dashboard will be overwritten
        new_dash: t.Dict[str, t.Any] = {
            "dashboard": dashboard,
            "overwrite": True,
        }

        old_dash = self.find_dashboard(dashboard["title"])

        # ** check a previous dashboard existence (same folder, same uid)
        if old_dash is None:
            new_dash["overwrite"] = self.overwrite
            dashboard["version"] = 1

        # * check the destination folder is General
        if re.match("general", self.grafana_folder, re.IGNORECASE):
            new_dash["folderId"] = 0
        else:
            # ** check 'custom' folder existence (custom != General)
            folder = self.get_folder(self.grafana_folder)
            if folder is None:
                folder = self.grafana_api.folder.create_folder(self.grafana_folder)

                if folder:
                    new_dash["folderId"] = folder["id"]
                else:
                    raise Exception("KO: grafana folder '{0}' creation failed.".format(self.grafana_folder))
            else:
                new_dash["folderId"] = folder["id"]

        # ** several case
        # read new folder1/dash1(uid1) => old folder1/dash1(uid1): classic update
        # b) read new folder_new/dash1(uid1) => old folder1/dash1(uid1): create new dash in folder_new
        #      => new folder_new/dash1(uid_new) if allow_new
        # c) read new folder_new/dash1(uid_new) => old folder1/dash1(uid1): create new in new folder folder_new
        #      => classic create (update)
        # d) read new folder1/dash1(uid_new) => old folder1/dash1(uid1)
        #      => new folder1/dash1(uid1) if overwrite
        if old_dash is not None:
            if "meta" in old_dash and "folderUrl" in old_dash["meta"]:
                old_dash["folderId"] = old_dash["meta"]["folderId"]
            elif "folderId" not in old_dash:
                old_dash["folderId"] = 0

            # case b) get a copy of an existing dash to a folder where dash is not present
            if new_dash["folderId"] != old_dash["folderId"]:
                # if new_dash['dashboard']['uid'] == old_dash['uid']:
                if self.allow_new:
                    new_dash["overwrite"] = False
                    # force the creation of a new dashboard
                    new_dash["dashboard"]["uid"] = None
                    new_dash["dashboard"]["id"] = None
                else:
                    raise GrafanaClient.GrafanaBadInputError(
                        "Dashboard with the same title already exists in another folder. "
                        "Use `allow_new` to permit creation in a different folder."
                    )
            # ** case d) send a copy to existing dash : update existing
            elif new_dash["folderId"] == old_dash["folderId"]:
                if (
                    "uid" not in new_dash["dashboard"]
                    or new_dash["dashboard"]["uid"] != old_dash["uid"]
                    or new_dash["dashboard"]["id"] != old_dash["id"]
                ):
                    if self.overwrite:
                        if not self.keep_uid:
                            new_dash["dashboard"]["uid"] = old_dash["uid"]
                        new_dash["dashboard"]["id"] = old_dash["id"]
                    else:
                        raise GrafanaClient.GrafanaBadInputError(
                            "Dashboard with the same title already exists in this folder with another uid. "
                            "Use `overwrite` to permit overwriting it."
                        )
        else:
            if not self.keep_uid:
                # force the creation of a new dashboard
                new_dash["dashboard"]["uid"] = None

            new_dash["dashboard"]["id"] = None
            new_dash["overwrite"] = False

        new_dash["message"] = "imported from {0}.".format(PKG_NAME)

        res = self.grafana_api.dashboard.update_dashboard(new_dash)
        if res["status"]:
            res = True
        else:
            res = False

        return res
