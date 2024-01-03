# Querying Azure Devops with OpenAI

This repo demonstrates how to query AzDO content using [Langchain integration with Azure OpenAI](https://python.langchain.com/docs/integrations/chat/azure_chat_openai).

Specifically, it defines custom [document loaders](https://python.langchain.com/docs/modules/data_connection/document_loaders/) for [user stories](./AzdoBacklogLoader.py) and [pull requests](./AzdoPullRequestLoader.py) to facilitate Q&A like:

```
What is the title and owner of the most recently completed user story?
```
```
Summarize Alice's comments on Bob's PR for work item 234.
```

_Note the techniques demonstrated in this repo are generalized and should be refined for specific use cases._

## Requirements

- Access to an AzDO project and [personal access token](https://learn.microsoft.com/en-us/azure/devops/organizations/accounts/use-personal-access-tokens-to-authenticate)

- An [Azure OpenAI Service](https://learn.microsoft.com/en-us/azure/ai-services/openai/overview) instance

- A deployed [embeddings model](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/models#embeddings)

- A deployed [GPT model](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/models#gpt-4-and-gpt-4-turbo-preview) (3.5 or 4)

- [Visual Studio Code](https://code.visualstudio.com/) and [Docker Desktop](https://www.docker.com/products/docker-desktop/) for devcontainer support

## Getting Started

- Clone this repo and open VS Code in the repo root folder. When prompted, re-open as a devcontainer

- In [main.ipynb](./main.ipynb) add your Azure OpenAI endpoint and key, as well as the names of your embeddings and GPT model deployments

- Also in [main.ipynb](./main.ipynb) add your AzDO URI, PAT, and project name

- In the last notebook cell, update the query as warranted for your use case

- Run all cells and observe the results

- Iterate on the query to coax relevant and accurate responses out of Azure OpenAI