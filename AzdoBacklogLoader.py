from typing import List

from langchain_core.documents import Document
from langchain.document_loaders.base import BaseLoader

from azure.devops.v7_1.work_item_tracking.models import Wiql

from bs4 import BeautifulSoup


class AzdoBacklogLoader(BaseLoader):
    """Load from Azure Devops backlog."""

    def __init__(self, azdo_org_uri: str, azdo_pat: str, azdo_project: str, days: int = 30):
        self.azdo_org_uri = azdo_org_uri
        self.azdo_pat = azdo_pat
        self.azdo_project = azdo_project
        self.days = days

    def load(self) -> List[Document]:
        """Load documents."""
        try:
            from azure.devops.credentials import BasicAuthentication
            from azure.devops.connection import Connection
        except ImportError as exc:
            raise ImportError(
                "Could not import azure devops python package. "
                "Please install it with `pip install azure-devops`."
            ) from exc

        auth = BasicAuthentication("", self.azdo_pat)
        conn = Connection(base_url=self.azdo_org_uri, creds=auth)

        wit_client = conn.clients.get_work_item_tracking_client()
        
        wiql = Wiql(query=f"""
                    SELECT
                        [System.Id]
                    FROM
                        WorkItems
                    WHERE
                        [System.TeamProject] = '{self.azdo_project}'
                        AND
                        [System.WorkItemType] = 'User Story'
                        AND
                        [System.ChangedDate] >= @today-{self.days}
                    ORDER BY
                        [System.ChangedDate] desc
                    """)

        items = wit_client.query_by_wiql(wiql).work_items

        documents = []

        if items:
            ids = [str(i.id) for i in items]
            work_items = wit_client.get_work_items(ids)
            for wi in work_items:
                documents.append(self._canonicalize(wi))

        return documents

    def _extract_text(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        for data in soup(["script", "style"]):
            data.decompose()
        return soup.get_text()
    
    def _get_value(self, field, item, default = ''):
        return item.fields[field] if field in item.fields else default

    def _canonicalize(self, item):

        title = self._get_value('System.Title', item)
        owner = self._get_value('System.AssignedTo', item)

        content = f"""
            work_item_id: {item.id}
            work_item_title: {title}
            work_item_created_date: {self._get_value('System.CreatedDate', item)}
            work_item_changed_date: {self._get_value('System.ChangedDate', item)}
            work_item_closed_date: {self._get_value('Microsoft.VSTS.Common.ClosedDate', item)}
            work_item_state: {self._get_value('System.State', item)}
            work_item_owner: {owner}

            work_item_description:
            {self._extract_text(self._get_value('System.Description', item, '<html></html>'))}

            work_item_acceptance_criteria:
            {self._extract_text(self._get_value('Microsoft.VSTS.Common.AcceptanceCriteria', item, '<html></html>'))}
        """

        metadata = {
            "id": item.id,
            "title": title,
            "owner": owner,
            "type": "backlog"
        }

        return Document(page_content=content, metadata=metadata)
