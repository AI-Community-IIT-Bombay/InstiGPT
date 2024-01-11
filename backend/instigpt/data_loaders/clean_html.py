import json
from typing import Union
import re

import grequests
from chromadb.api import ClientAPI
from langchain_core.embeddings import Embeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from bs4 import BeautifulSoup, PageElement

from instigpt import config


def get_content(node: PageElement) -> str:
    name = node.name
    if name is None:
        if str(node) == "\n":
            return " "
        return node.text
    elif name == "a":
        # return get_content(node)
        if node.text != "":
            return f"{node.text} ({node.get('href')}) "
        else:
            text = " ".join([get_content(child) for child in node.children]).replace(
                "\n", ""
            )
            return f"{text} ({node.get('href')}) "
    elif name == "nav" or name == "footer" or name == "img" or name == "svg":
        return ""

    content = ""
    for child in node.children:
        content += get_content(child)

    return content


def load_html_data(
    client: ClientAPI,
    embeddings: Embeddings,
    data_path: Union[str, list[str]],
) -> int:
    """Fetches the html content from the link(s), extracts requried content and
    then stores it in the database along with its embeddings.

    returns: int: number of dicuments stored in the database
    """
    if type(data_path) == str:
        data_path = [data_path]

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,
        chunk_overlap=200,
        length_function=len,
        is_separator_regex=True,
    )
    coll = client.get_or_create_collection(config.COLLECTION_NAME)
    num_docs_added = 0

    reqs = [grequests.get(link) for link in data_path]
    for res in grequests.map(reqs, size=20):
        if res is None:
            continue

        html = res.text
        soup = BeautifulSoup(html, "lxml")
        content = "\n".join([get_content(child) for child in soup.body.children])  # type: ignore
        content = re.sub(r"\s{2,}", "\n", content)
        docs = text_splitter.split_text(content)
        metadatas = [{"source": res.url} for _ in range(len(docs))]
        ids = [f"{res.url}-{i}" for i in range(len(docs))]

        coll.add(
            documents=docs,
            embeddings=embeddings.embed_documents(docs),  # type: ignore
            metadatas=list(metadatas),
            ids=ids,
        )
        num_docs_added += len(docs)

    return num_docs_added
