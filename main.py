# -*- coding: utf-8 -*-
# 导入所需的库
from flask import Flask, render_template, abort, request
from markdown.inlinepatterns import InlineProcessor
from markdown.extensions import Extension
import xml.etree.ElementTree as etree
import os
import time
import glob
import markdown
import re
import json

# 创建flask应用对象
app = Flask(__name__)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'),404

class DelInlineProcessor(InlineProcessor):
    def handleMatch(self, m, data):
        el = etree.Element('del')
        el.text = m.group(1)
        return el, m.start(0), m.end(0)

class DelExtension(Extension):
    def extendMarkdown(self, md):
        DEL_PATTERN = r'~~(.*?)~~'
        md.inlinePatterns.register(DelInlineProcessor(DEL_PATTERN, md), 'del', 175)

def get_article_title(path):
    # 打开并读取文件内容（只读取第一行）
    with open(path, "r", encoding='utf-8') as f:
        first_line = f.readline()
    # 使用正则表达式匹配HTML注释中的内容作为标题（假设注释格式为<!-- title -->）
    match = re.search(r"<!--\s*(.+?)\s*-->", first_line)
    if match:
        title = match.group(1)
    else:
        title = os.path.basename(path).replace(".md", "")
    return title


def get_config(key):
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    try:
        value = config[key]
    except KeyError:
        return None
    return value

POSTS_PER_PAGE = get_config("posts_per_page")

def get_file_create_time(path, style="%Y-%m-%d"):
    time_array = time.localtime(os.stat(path).st_mtime)
    styled_time = time.strftime(style, time_array)
    return styled_time


@app.route("/<path:filename>")
def show_post(filename):
    # 拼接文件路径，添加.md扩展名
    file_path = "posts/" + filename + ".md"
    if not os.path.exists(file_path):
        abort(404)
    # 打开文件，读取内容
    with open(file_path, "r", encoding='utf-8') as f:
        content = f.read()
    # 使用markdown模块将内容转换为html
    html = markdown.markdown(content, extensions=[
                             "markdown.extensions.extra","markdown.extensions.sane_lists", DelExtension()])
    title = get_article_title(file_path)
    date = get_file_create_time(file_path)
    output = render_template(
        "article.html", content=html, title=title, date=date, main_title=get_config("title"), links=get_config("links"))
    # 返回最终的html页面
    return output


@app.route("/")
def show_home():
    # 获取URL参数中的page值，默认为1
    page = request.args.get("page", 1, type=int)
    # 获取posts目录下所有的Markdown文件，并按照创建时间排序
    posts = sorted(glob.glob("posts/*.md"), key=os.path.getctime, reverse=True)
    # 计算总共有多少页
    total_pages = (len(posts) - 1) // POSTS_PER_PAGE + 1
    # 如果page值超出范围，返回404错误
    if page < 1 or page > total_pages:
        abort(404)
    # 根据page值获取对应的文件列表
    start = (page - 1) * POSTS_PER_PAGE
    end = start + POSTS_PER_PAGE
    posts = posts[start:end]

    # 创建一个空列表来存储文章标题和链接地址（相对路径）
    articles = []
    for post in posts:
        # 链接地址（相对路径），去掉“.md”后缀，并加上“/”前缀
        link = "/" + os.path.basename(post).replace(".md", "")
        title = get_article_title(post)
        date = get_file_create_time(post)
        articles.append((title, link, date))

    # 使用home.html模板，并传入articles和page作为参数（还可以传入其他参数，比如total_pages等）
    return render_template("./home.html", total_pages=total_pages, articles=articles, page=page, main_title=get_config("title"), links=get_config("links"))


# 运行flask应用
if __name__ == "__main__":
    from waitress import serve
    serve(app, host="127.0.0.1", port=7000)