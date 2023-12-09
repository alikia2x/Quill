import sqlite3

import markdown
import time
from flask import Flask, render_template, request, jsonify


app = Flask(__name__)
# 数据库文件
DATABASE = 'db.sqlite'


# 辅助函数，用于查询数据库并返回结果
def query_db(query, args=(), one=False):
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query, args)
    rv = cur.fetchall()
    conn.close()
    return (rv[0] if rv else None) if one else rv


def get_config(key, subkey="value"):
    query = "SELECT * FROM info WHERE key=?"
    data = query_db(query, [key], one=True)
    if data:
        return data[subkey]
    else:
        return None


def time_cost(t):
    return str(round((time.time() - t) * 1000, 3))


# 首页路由
@app.route('/', methods=['GET'])
def index():
    t = time.time()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    # 快速获取数据库中的文章数量
    query = "SELECT COUNT(*) FROM articles"
    total = query_db(query)[0][0]
    total_pages = total // per_page + (1 if total % per_page > 0 else 0)

    page = max(1, min(page, total_pages))
    per_page = max(1, min(per_page, total))

    # 查询数据库，按modify_time降序排列，获取最新的文章
    query = "SELECT id, title, modify_time, summary FROM articles ORDER BY modify_time DESC LIMIT ? OFFSET ?"
    articles = query_db(query, (per_page, (page - 1) * per_page))

    title = get_config("site_title")

    return render_template('index.html', articles=articles, res_time=time_cost(t), title=title,
                           page=page, per_page=per_page, total_pages=total_pages)


# 文章详情页路由
@app.route('/article/<int:id>', methods=['GET'])
def article(id):
    t = time.time()
    # 查询指定ID的文章内容
    article_detail = query_db("SELECT content, title FROM articles WHERE id=?", [id], one=True)

    if article_detail:
        # 将Markdown渲染为HTML
        html_content = markdown.markdown(article_detail['content'], extensions=['pymdownx.extra','markdown_del_ins','pymdownx.superfences','pymdownx.highlight'])
        return render_template('article.html', content=html_content, title=article_detail['title'],
                               site_title=get_config("site_title"), homepage=get_config("homepage"),
                               res_time=time_cost(t), lang=get_config("lang"))
    else:
        return render_template('404.html'), 404


@app.route('/article/', methods=['POST'])
def create_article():
    try:
        title = request.form['title']
        content = request.form['content']

        conn = sqlite3.connect('db.sqlite')
        cursor = conn.cursor()

        cursor.execute("INSERT INTO articles (title, content) VALUES (?, ?)", (title, content))
        new_article_id = cursor.lastrowid
        # 提交事务，关闭数据库连接
        conn.commit()
        conn.close()

        response_data = {
            'id': new_article_id,
            'title': title
        }

        return jsonify(response_data), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 400


if __name__ == '__main__':
    app.run(debug=True)
