from typing import List

from langchain_core.documents import Document
from langchain.document_loaders.base import BaseLoader

from azure.devops.v7_1.git.models import GitPullRequestSearchCriteria

from bs4 import BeautifulSoup


class AzdoPullRequestLoader(BaseLoader):
    """Load from Azure Devops pull requests."""

    def __init__(self, azdo_org_uri: str, azdo_pat: str, azdo_project: str):
        self.azdo_org_uri = azdo_org_uri
        self.azdo_pat = azdo_pat
        self.azdo_project = azdo_project

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

        git_client = conn.clients.get_git_client()
        wit_client = conn.clients.get_work_item_tracking_client()

        documents = []

        for repo in git_client.get_repositories(self.azdo_project):
            search_criteria = GitPullRequestSearchCriteria(repository_id=repo.id, status='all')
            for pr in git_client.get_pull_requests(repo.id, search_criteria):
                documents.extend(self._canonicalize(pr, git_client, wit_client))

        return documents

    def _extract_text(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        for data in soup(["script", "style"]):
            data.decompose()
        return soup.get_text()

    def _canonicalize_commits(self, pr, git_client):
        
        commits = []

        for commit in git_client.get_pull_request_commits(pr.repository.id, pr.pull_request_id):
            
            content = f"""
                pull_request_commit_id: {commit.commit_id}
                pull_request_commit_author: {commit.author.name}
                pull_request_commit_date: {commit.author.date}
                pull_request_commit_message: {self._extract_text(commit.comment)}
                pull_request_id: {pr.pull_request_id}
            """

            metadata = {
                "author": commit.author.name,
                "pull_request_id": pr.pull_request_id,
                "type": "pull_request_commit",
            }

            commits.append(Document(page_content=content, metadata=metadata))

        return commits

    def _canonicalize_comments(self, pr, git_client):

        comments = []

        for thread in git_client.get_threads(pr.repository.id, pr.pull_request_id):
            if not thread.is_deleted:
                for comment in thread.comments:
                    
                    content = f"""
                        pull_request_comment_id: {comment.id}
                        pull_request_comment_author: {comment.author.display_name}
                        pull_request_comment_author_unique_name: {comment.author.unique_name}
                        pull_request_comment_published_date: {comment.published_date}
                        pull_request_comment_text: {self._extract_text(comment.content) if comment.content else ''}
                        pull_request_id: {pr.pull_request_id}
                    """

                    metadata = {
                        "author": comment.author.display_name,
                        "pull_request_id": pr.pull_request_id,
                        "type": "pull_request_comment",
                    }

                    comments.append(Document(page_content=content, metadata=metadata))

        return comments

    def _canonicalize_work_items(self, pr, git_client, wit_client):

        work_items = []

        for work_item_ref in git_client.get_pull_request_work_item_refs(pr.repository.id, pr.pull_request_id):
            for work_item in wit_client.get_work_items([work_item_ref.id]):

                content = f"""
                    pull_request_work_item_id: {work_item.id}
                    pull_request_work_item_title: {work_item.fields['System.Title']}
                    pull_request_work_item_owner: {work_item.fields['System.AssignedTo']}
                    pull_request_work_item_state: {work_item.fields['System.State']}
                    pull_request_id: {pr.pull_request_id}
                """

                metadata = {
                    "author": work_item.fields['System.AssignedTo'],
                    "pull_request_id": pr.pull_request_id,
                    "type": "pull_request_work_item",
                }

                work_items.append(Document(page_content=content, metadata=metadata))

        return work_items

    def _canonicalize(self, pr, git_client, wit_client):

        content = f"""
            pull_request_id: {pr.pull_request_id}
            pull_request_title: {pr.title}
            pull_request_owner: {pr.created_by.display_name}
            pull_request_status: {pr.status}
            pull_request_created_date: {pr.creation_date}
            pull_request_closed_date: {pr.closed_date}

            pull_request_description:
            {self._extract_text(pr.description) if pr.description else ''}
        """

        metadata = {
            "id": pr.pull_request_id,
            "owner": pr.created_by.display_name,
            "type": "pull_request",
        }

        docs = []

        docs.append(Document(page_content=content, metadata=metadata))

        docs.extend(self._canonicalize_commits(pr, git_client))
        docs.extend(self._canonicalize_comments(pr, git_client))
        docs.extend(self._canonicalize_work_items(pr, git_client, wit_client))

        return docs
