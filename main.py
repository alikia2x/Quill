# -*- coding: utf-8 -*-
# 导入所需的库
import asyncio
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
import requests
from compressor import compress

compress()

fenced_code_pattern = re.compile(
    r"^(`{3,})(\w*)\n(.*?)\n(`{3,})$", re.MULTILINE | re.DOTALL)

# 创建flask应用对象
app = Flask(__name__)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


class DelInlineProcessor(InlineProcessor):
    def handleMatch(self, m, data):
        el = etree.Element('del')
        el.text = m.group(1)
        return el, m.start(0), m.end(0)


class DelExtension(Extension):
    def extendMarkdown(self, md):
        DEL_PATTERN = r'~~(.*?)~~'
        md.inlinePatterns.register(
            DelInlineProcessor(DEL_PATTERN, md), 'del', 175)


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


def replace_fenced_code(match):
    start = match.group(1)  # 开始的反引号
    code = match.group(3)  # 代码内容
    end = match.group(4)  # 结束的反引号
    # 添加class属性到开始的反引号后面
    new_start = start + " {class=\"fenced_code\"}"
    # 返回替换后的字符串
    return "\n".join([new_start, code, end])


def write_log(postname,ip,device):
    req_time = time.time()
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}")
        country = response.json()["country"]
    except:
        country = "Unknown"

    try:
        # 尝试打开文件
        f = open("log.json")
    except FileNotFoundError:
        # 如果文件不存在，则新建文件并写入空的json对象
        f = open("log.json", "w")
        json.dump({}, f)
    else:
        # 如果文件存在，则读取json数据
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            f.close()
            f = open("log.json", "w")
            json.dump({}, f)
            data = {}
    finally:
        # 无论是否发生异常，都要关闭文件
        f.close()

    # 打开json文件，如果不存在则创建一个新的文件
    with open("log.json", "w") as f:
        # 检查是否有该postname的键，如果没有则创建一个空列表
        if postname not in data:
            data[postname] = []
        # 将请求记录添加到对应的列表中
        data[postname].append({"time": req_time, "ip": ip, "device": device, "country": country})
        # 将更新后的数据写回到文件中
        json.dump(data, f)

# 定义一个路由，处理/analytics/<postname>的请求，并返回访问量统计页面
@app.route("/analytics/<path:filepath>")
def analytics(filepath):
    # 打开json文件，读取数据，如果不存在则返回错误信息
    try:
        with open("log.json", "r") as f:
            data = json.load(f)
            logs = data[filepath]
    except:
        return "No such post or log file."

    import datetime
    import collections

    # 获取当前日期
    today = datetime.date.today()

    # 定义统计变量
    today_pv = 0  # 今天的访问量
    week_pv = 0  # 最近7天的访问量
    month_pv = 0  # 最近30天的访问量
    total_pv = 0 # 总访问量
    device_counter = collections.Counter()  # 设备出现次数的计数器
    browser_counter = collections.Counter()  # 浏览器出现次数的计数器
    location_counter = collections.Counter()  # 地理位置出现次数的计数器
    os_counter = collections.Counter() # 操作系统出现次数的计数器
    today_ip_set = set() # 今天出现过的ip地址集合
    week_ip_set = set() # 最近7天出现过的ip地址集合
    month_ip_set = set() # 最近30天出现过的ip地址集合
    all_ip_set = set() # 所有ip地址集合

    # 遍历json数据中的每一条记录
    for record in data[filepath]:
        # 获取记录中的时间戳，ip地址和设备信息
        time_stamp = record["time"]
        device_info = record["device"]
        country = record["country"]
        ip=record["ip"]

        # 将时间戳转换为日期对象
        date_obj = datetime.date.fromtimestamp(time_stamp)

        # 判断日期是否在今天，最近7天或最近30天内，并更新相应的访问量变量和ip地址集合变量
        if date_obj == today:
            today_pv += 1
            today_ip_set.add(ip)
        if (today - date_obj).days < 7:
            week_pv += 1
            week_ip_set.add(ip)
        if (today - date_obj).days < 30:
            month_pv += 1
            month_ip_set.add(ip)
        
        total_pv+=1
        all_ip_set.add(ip)

        import user_agents
        ua=user_agents.parse(device_info)
        # 解析设备信息中的设备类型和浏览器类型，并更新相应的计数器变量
        device_type = ua.device.family
        browser_type = ua.browser.family
        os_type = ua.os.family

        if ua.is_pc:
            device_type = "PC"

        location_counter[country] += 1
        device_counter[device_type] += 1
        browser_counter[browser_type] += 1
        os_counter[os_type] += 1

    # 计算独立访客数变量
    today_uv = len(today_ip_set) # 今天的独立访客数
    week_uv = len(week_ip_set) # 最近7天的独立访客数
    month_uv = len(month_ip_set) # 最近30天的独立访客数
    total_uv = len(all_ip_set)
    return render_template("analytics.html", main_title=get_article_title("posts/" + filepath + ".md"), filepath=filepath, 
                           today_pv=today_pv, week_pv=week_pv, month_pv=month_pv, total_pv=total_pv,
                           today_uv=today_uv, week_uv=week_uv, month_uv=month_uv, total_uv=total_uv,
                           device_counter=device_counter, browser_counter=browser_counter, location_counter=location_counter, os_counter=os_counter)

@app.route("/<path:filename>")
def show_post(filename):
    # 拼接文件路径，添加.md扩展名
    file_path = "posts/" + filename + ".md"
    if not os.path.exists(file_path):
        abort(404)
    # 打开文件，读取内容
    with open(file_path, "r", encoding='utf-8') as f:
        content = f.read()

    # 预处理，用于解决围栏代码块的样式问题
    content = fenced_code_pattern.sub(replace_fenced_code, content)
    # 使用markdown模块将内容转换为html
    html = markdown.markdown(content, extensions=[
                             "markdown.extensions.sane_lists", "markdown.extensions.extra", DelExtension()])
    title = get_article_title(file_path)
    date = get_file_create_time(file_path)
    output = render_template(
        "article.html", content=html, title=title, date=date, filename=filename, main_title=get_config("title"), links=get_config("links"), copyright=get_config("copyright"))

    if get_config("use_proxy"):
        ip=request.headers.get("X-Forwarded-For")
    else:
        ip=request.remote_addr
    import multiprocessing
    log_process=multiprocessing.Process(target=write_log, args=(filename,ip,request.user_agent.string,))
    log_process.start()
    
    return output


@app.route("/")
def show_home():
    # 获取URL参数中的page值，默认为1
    page = request.args.get("page", 1, type=int)
    # 获取posts目录下所有的Markdown文件，并按照修改时间排序
    posts = sorted(glob.glob("posts/*.md"), key=os.path.getmtime, reverse=True)
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
    # 对于Debug，请使用如下代码
    #app.run(host="0.0.0.0", port=80, debug=True)
    from waitress import serve
    serve(app, host="127.0.0.1", port=7000)
