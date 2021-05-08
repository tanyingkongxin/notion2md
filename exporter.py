import os
import requests


# from datetime import datetime


class PageBlockExporter:
    def __init__(self, url, client, directory):
        self.client = client
        self.page = self.client.get_block(url)
        self.file_name = self.page.title

        self.md = ""
        self.dir = directory + self.file_name + '/'
        # self.image_dir = ""
        # self.download_dir = ""
        self.sub_exporters = []

    def export(self):
        # create folder with file name
        if not (os.path.isdir(self.dir)):
            os.makedirs(os.path.join(self.dir))

        # write to markdown file
        file_path = os.path.join(self.dir, self.file_name + '.md')
        with open(file_path, 'w', encoding='utf-8') as f:
            self.page2md()
            f.write(self.md)
            f.close()

        # export all sub-page recursively
        for sub_exporter in self.sub_exporters:
            sub_exporter.export()

    # def create_image_foler(self):
    #     """create image output directory
    #     """
    #     self.image_dir = os.path.join(self.dir, 'image/')
    #     if not (os.path.isdir(self.image_dir)):
    #         os.makedirs(os.path.join(self.image_dir))

    #
    # def image_export(self, url, count):
    #     """make image file based on url and count.
    #
    #       Args:
    #         url(Stirng): url of image
    #         count(int): the number of image in the page
    #
    #       Returns:
    #         image_path(String): image_path for the link in markdown
    #     """
    #     if self.image_dir is "":
    #         self.create_image_foler()
    #     image_path = self.image_dir + 'img_{0}.png'.format(count)
    #     r = requests.get(url, allow_redirects=True)
    #     open(image_path, 'wb').write(r.content)
    #     return image_path

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
        params = {'tap_count': 0, 'img_count': 0, 'num_index': 0}
        if page is None:
            page = self.page
        for i, block in enumerate(page.children):
            try:
                self.block2md(block, params)
            except Exception as e:
                print("[Block exception]: ", e)
                self.md += ""
        # self.md = self.md[:-1]  # why do this ?

    def block2md(self, block, params):
        if params['tap_count'] != 0:
            self.md += '\n'
            for i in range(params['tap_count']):
                self.md += '\t'
        try:
            btype = block.type
        except Exception as e:
            print('[block type error] ', e)

        if btype != "numbered_list":
            params['num_index'] = 0
        try:
            bt = block.title
        except:
            pass

        if btype == 'header':
            self.md += "# " + block.title
        elif btype == "sub_header":
            self.md += "## " + block.title
        elif btype == "sub_sub_header":
            self.md += "### " + block.title
        elif btype == 'page':
            # self.create_sub_folder()
            sub_url = block.get_browseable_url()
            exporter = PageBlockExporter(sub_url, self.client, self.dir)
            # print("[Log]: test for title of subpage, {}".format(block.title))
            try:
                if "https:" in block.icon:
                    icon = "!" + link_format("", block.icon)
                else:
                    icon = block.icon
            except Exception as e:
                print('[icon]', e)
                icon = ""
            self.sub_exporters.append(exporter)
            self.md += icon + link_format(exporter.file_name, './{0}/{0}.md'.format(block.title))
        elif btype == 'text':
            try:
                self.md += block.title
            except:
                self.md += ""
        elif btype == 'bookmark':
            self.md += link_format(bt, block.link)
        elif btype == "video" or btype == "file" or btype == "audio" or btype == "pdf" or btype == "gist":
            self.md += link_format(block.source, block.source)
        elif btype == "bulleted_list" or btype == "toggle":
            self.md += '- ' + block.title
        elif btype == "numbered_list":
            params['num_index'] += 1
            self.md += str(params['num_index']) + '. ' + block.title
        elif btype == "code":
            self.md += "``` " + block.language.lower() + "\n" + block.title + "\n```"
        elif btype == "equation":
            self.md += "$$" + block.latex + "$$"
        elif btype == "divider":
            self.md += "---"
        elif btype == "to_do":
            if block.checked:
                self.md += "- [x] " + bt
            else:
                self.md += "- [ ] " + bt
        elif btype == "quote":
            self.md += "> " + bt
        elif btype == "column" or btype == "column_list":
            self.md += ""
        elif btype == "collection_view":
            collection = block.collection
            self.md += self.make_table(collection)
        elif btype == "callout":
            self.md += "``` " + "\n" + block.title + "\n```"
        elif btype == "table_of_contents":
            self.md += "[TOC]"
        else:
            print('Unhandled block type: ', btype)

        if block.children and btype != 'page':
            params['tap_count'] += 1
            num_index = params['num_index']
            params['num_index'] = 0
            for child in block.children:
                self.block2md(child, params)
            params['tap_count'] -= 1
            params['num_index'] = num_index
        if params['tap_count'] == 0:
            self.md += "\n\n"

    def make_table(self, collection):
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
                    content = self.page2md(row)
                else:
                    content = row.get_property(column)
                if str(type(content)) == "<class 'list'>":
                    content = ', '.join(content)
                if str(type(content)) == "<class 'datetime.datetime'>":
                    content = content.strftime('%b %d, %Y')
                if column == "Name":
                    row_content.insert(0, content)
                else:
                    row_content.append(content)
            table.append(row_content)
        return table_to_markdown(table)


def link_format(name, url):
    """make markdown link format string
    """
    return "[" + name + "]" + "(" + url + ")"


def table_to_markdown(table):
    md = ""
    md += join_with_vertical(table[0])
    md += "\n---|---|---\n"
    for row in table[1:]:
        if row != table[1]:
            md += '\n'
        md += join_with_vertical(row)
    return md


def join_with_vertical(list):
    return " | ".join(list)




# def filter_source_url(block):
#     try:
#         return block.get('properties')['source'][0][0]
#     except:
#         return block.title
