import os, re

def css_minify(css):
    # 删除注释
    css = re.sub(r"/\*.*?\*/", "", css)
    # 删除空格和空行
    css = re.sub(r"\s+", " ", css)
    # 删除不必要的分号和花括号
    css = re.sub(r";\s*}", "}", css)
    # 删除不必要的冒号和分号
    css = re.sub(r":\s*;", ":", css)
    # 去掉首尾的空格
    css = css.strip()
    return css

def html_minify(html):
    # 删除空行、注释和tab
    html = re.sub(r"\n", "", html)
    html = re.sub(r"<!--.*?-->", "", html)
    html = re.sub(r"\t", "", html)
    # 去掉首尾的空格
    html = html.strip()
    return html

def compress():
    # 遍历当前目录下的css目录
    for html_file in os.listdir("html"):
        # 检查是否是.css文件
        if html_file.endswith(".html"):
            css_file = html_file.replace(".html", ".css")
            # 读取html模板内容
            with open(os.path.join("html", html_file), "r", encoding="utf-8") as f:
                html_content = f.read()
            if os.path.exists(os.path.join("css", css_file)):
                # 读取css文件
                with open(os.path.join("css", css_file), "r") as f:
                    css_content = f.read()
                # 压缩css文件并获取结果
                compressed_css = css_minify(css_content)
                # 替换[compressed-css]为压缩后的文本
                html_content = html_content.replace("[compressed-css]", "<style>"+compressed_css+"</style>")
            # 压缩html文件并获取结果
            compressed_html = html_minify(html_content)
            # 写入到templates目录下的对应文件（如果不存在则创建）
            with open(os.path.join("templates", html_file), "w", encoding="utf-8") as f:
                f.write(compressed_html)

compress()
