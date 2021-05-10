import os
import requests
from notion.collection import NotionDate
from notion.user import User
import datetime


class PageBlockExporter(object):
    def __init__(self, url, client, directory, isCollection=False):
        self.client = client
        self.page = self.client.get_block(url)
        self.file_name = self.page.title

        self.md = ""
        self.dir = directory + self.file_name + '/'
        self.image_dir = ""
        # self.download_dir = ""
        self.sub_exporters = []
        self.isCollection = isCollection

    def export(self):
        # create folder with file name
        if not (os.path.isdir(self.dir)):
            os.makedirs(os.path.join(self.dir))

        # write to markdown file
        file_path = os.path.join(self.dir, self.file_name + '.md')
        with open(file_path, 'w', encoding='utf-8') as f:
            self.md = self.page2md()
            f.write(self.md)
            f.close()

        # export all sub-page recursively
        for sub_exporter in self.sub_exporters:
            sub_exporter.export()

    # def create_download_foler(self):
    #     """create download output directory
    #     """
    #     self.download_dir = os.path.join(self.dir, 'download/')
    #     print(self.download_dir)
    #     if not(os.path.isdir(self.download_dir)):
    #         os.makedirs(os.path.join(self.download_dir))

    # def downlaod_file(self, url, file_name):
    #     """download a file in the page.
    #
    #       Args:
    #         url(Stirng): url of the downlaod file
    #         file_name(String): name of the file
    #
    #       Returns:
    #         None
    #     """
    #     if self.download_dir is "":
    #         self.create_download_foler()
    #
    #     try:
    #         download_path = self.download_dir + file_name
    #     except Exception as e:
    #         print(e)
    #     r = requests.get(url, allow_redirects=True)
    #     open(download_path, 'wb').write(r.content)

    def page2md(self, page=None):
        """change notion's block to markdown string
        """
        result = ""
        params = {'tap_count': 0, 'img_count': 0, 'num_index': 0}
        if page is None:
            page = self.page

        if self.isCollection:
            result += self._make_table(page.collection)
        else:
            for i, block in enumerate(page.children):
                try:
                    result += self.block2md(block, params)
                except Exception as e:
                    print("[Block exception]: ", e)
        # self.md = self.md[:-1]
        return result

    def block2md(self, block, params):
        result = ""
        if params['tap_count'] != 0:
            result += '\n'
            for i in range(params['tap_count']):
                result += '\t'

        btype = block.type
        if btype != "numbered_list":
            params['num_index'] = 0

        if btype == 'header':
            result += "# " + block.title
        elif btype == "sub_header":
            result += "## " + block.title
        elif btype == "sub_sub_header":
            result += "### " + block.title
        elif btype == 'page':
            sub_url = block.get_browseable_url()
            exporter = PageBlockExporter(sub_url, self.client, self.dir)
            try:
                if block.icon is None:
                    icon = ""
                elif "https:" in block.icon:
                    icon = "!" + link_format("", block.icon)
                else:
                    icon = block.icon
            except Exception as e:
                print('[icon]', e)
                icon = ""
            self.sub_exporters.append(exporter)
            result += icon + link_format(exporter.file_name, './{0}/{0}.md'.format(block.title))
        elif btype == 'text':
            try:
                result += self._filter_mentioned_page(block)
            except:
                pass
        elif btype == 'bookmark':
            result += link_format(block.title, block.link)
        elif btype == 'image':
            params['img_count'] += 1
            try:
                img_name = self._image_export(block.source, params['img_count'])
                result += "!" + link_format(img_name, './image/' + img_name)
            except Exception as e:
                print('[Image]', e)
        elif btype == "video" or btype == "file" or btype == "audio" or btype == "pdf" or btype == "gist":
            result += link_format(block.source, block.source)
        elif btype == "bulleted_list" or btype == "toggle":
            result += '- ' + self._filter_mentioned_page(block)
        elif btype == "numbered_list":
            params['num_index'] += 1
            result += str(params['num_index']) + '. ' + self._filter_mentioned_page(block)
        elif btype == "code":
            result += "``` " + block.language.lower() + "\n" + self._filter_mentioned_page(block) + "\n```"
        elif btype == "equation":
            result += "$$" + block.latex + "$$"
        elif btype == "divider":
            result += "---"
        elif btype == "to_do":
            if block.checked:
                result += "- [x] " + self._filter_mentioned_page(block)
            else:
                result += "- [ ] " + self._filter_mentioned_page(block)
        elif btype == "quote":
            result += "> " + self._filter_mentioned_page(block)
        elif btype == "column" or btype == "column_list":
            result += ""
        elif btype == "collection_view":
            collection = block.collection
            result += self._make_table(collection)
        elif btype == 'collection_view_page':
            sub_url = block.get_browseable_url()
            exporter = PageBlockExporter(sub_url, self.client, self.dir, True)
            self.sub_exporters.append(exporter)
            result += link_format(exporter.file_name, './{0}/{0}.md'.format(block.title))
        elif btype == "callout":
            result += "> 💡 " + self._filter_mentioned_page(block)
            # result += "``` " + "\n" + self._filter_mentioned_page(block) + "\n```"
        elif btype == "table_of_contents":
            result += "[TOC]"
        else:
            print('Unhandled block type: ', btype)

        if block.children and btype != 'page':
            params['tap_count'] += 1
            num_index = params['num_index']
            params['num_index'] = 0
            for child in block.children:
                result += self.block2md(child, params)
            params['tap_count'] -= 1
            params['num_index'] = num_index
        if params['tap_count'] == 0:
            result += "\n\n"
        return result

    def _filter_mentioned_page(self, block):
        mentioned_page_list = []
        title = block.title
        if title is "":
            return ""
        try:
            for content in block.get('properties')['title']:
                if content[0] == '‣':
                    mentioned_page_list.append("[[{0}]]".format(self.client.get_block(content[1][0][1]).title))
        except Exception as e:
            print(block.title, '[_filter_mentioned_page]', e)
        for i in range(len(mentioned_page_list)):
            title = title.replace('‣', mentioned_page_list[i])
        return title

    def _make_table(self, collection):
        columns = []
        row_blocks = collection.get_rows()
        for proptitle in row_blocks[0].schema:
            prop = proptitle['name']
            if prop == "Name":
                columns.insert(0, prop)
            else:
                columns.append(prop)
        table = [columns]
        for row in row_blocks:
            row_content = []
            for column in columns:
                if column == "Name" and row.get("content") is not None:
                    sub_url = row.get_browseable_url()
                    exporter = PageBlockExporter(sub_url, self.client, self.dir)
                    self.sub_exporters.append(exporter)
                    content = "[[{0}]]".format(row.get_property(column))
                else:
                    content = row.get_property(column)
                if isinstance(content, list):
                    # when the property type of column is Person
                    if len(content) > 0 and isinstance(content[0], User):
                        content = [user.full_name for user in content]
                    else:
                        content = ', '.join(content)
                elif isinstance(content, int):
                    content = str(content)
                elif isinstance(content, NotionDate):
                    if content.end is None:
                        content = str(content.start)
                    else:
                        content = str(content.start) + " -> " + str(content.end)
                elif isinstance(content, User):
                    content = content.full_name
                elif isinstance(content, datetime.datetime):
                    content = content.strftime("%Y-%m-%d %H:%M:%S")

                if column == "Name":
                    row_content.insert(0, content)
                else:
                    row_content.append(content)
            table.append(row_content)
        return table_to_markdown(table)

    def _image_export(self, url, count):
        if self.image_dir is "":
            self.image_dir = os.path.join(self.dir, 'image/')
            if not (os.path.isdir(self.image_dir)):
                os.makedirs(os.path.join(self.image_dir))

        image_name = 'img_{0}.png'.format(count)
        r = requests.get(url, allow_redirects=True)
        open(self.image_dir + image_name, 'wb').write(r.content)
        return image_name


def link_format(name, url):
    """ make markdown link format string """
    return "[" + name + "]" + "(" + url + ")"


def table_to_markdown(table):
    """ change `table` to markdown table format string """
    md = "| " + " | ".join(table[0]) + " |\n"
    md += "| ---- " * len(table[0]) + "|\n"
    for row in table[1:]:
        md += "| " + " | ".join(row) + " |\n"
    return md
