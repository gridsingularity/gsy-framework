import os
import shutil
import tempfile

import requests


class DefaultCDSDownloader:
    """Handle CDS file download"""

    def __init__(self):
        self.workdir = tempfile.mkdtemp()
        self.cds_file_path = os.path.join(self.workdir, "CommunityDataSheet.xlsx")

    def download(self):
        """Download cds file to temp dir"""
        header = {
            "Authorization": f"Bearer {os.environ['GITHUB_ACCESS_TOKEN']}",
            "X-GitHub-Api-Version": "2022-11-28",
            "Accept": "application/vnd.github.raw+json",
        }
        url = (
            f"https://api.github.com/repos/gridsingularity/gsy-web/contents/config/static/"
            f"CommunityDataSheet.xlsx?ref={os.environ.get('TARGET_BRANCH', 'master')}"
        )
        response = requests.get(url, headers=header)
        if response.status_code == 200:
            with open(self.cds_file_path, "wb") as file:
                file.write(response.content)
            return

        assert False, (
            f"Default CDS could not be downloaded because of: "
            f"{response.status_code}; {response.json()}"
        )

    def cleanup(self):
        """Remove temporary directory."""
        shutil.rmtree(self.workdir)
