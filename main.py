import os
from pathlib import Path
from notion.client import NotionClient
import json
from exporter import PageBlockExporter


def parse_token():
    try:
        with open('./notion2md_output/notion_token.json', 'r') as json_read:
            data = json.load(json_read)
        token = data["token"]
        client = NotionClient(token_v2=token)
        return client
    except OSError as e:
        print(e)
        token = ""

    while token is "":
        token = input("Enter Token_v2: ")
        try:
            client = NotionClient(token_v2=token)
            with open("./notion2md_output/notion_token.json", 'w') as json_make:
                json.dump({"token": token}, json_make, indent=4)
            return client
        except:
            print("[Error] Invaild Token_v2. Enter Token_v2 again")
            token = ""


def notion_to_markdown(token_v2="", url="", output_folder='./notion2md_output/'):
    """
    export notion page to markdown file
    :param token_v2: token_v2 of your notion account
    :param url: notion page url
    :param output_folder: the directory of output file
    """
    if not (os.path.isdir(output_folder)):
        Path(output_folder).mkdir()
    if token_v2 == "":
        client = parse_token()
    else:
        client = NotionClient(token_v2=token_v2)
    if url == "":
        url = input("Enter Notion Page Url: ")

    # export
    exporter = PageBlockExporter(url, client, output_folder)
    exporter.export()

    print("\nExporter successfully exported notion page to markdown")


if __name__ == "__main__":
    notion_to_markdown(url="https://www.notion.so/tanying/8e21f0239e6649ecb5c69fc4b79e3b95")
