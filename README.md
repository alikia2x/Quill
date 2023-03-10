# 素笔

素笔是一个开源、轻量、简洁的个人博客框架.

它使用Flask框架，并借助markdown库实现Markdown的渲染.

它最大的优势是“轻”，所有的模板文件均在3KB以内，没有JavaScript，没有额外的CSS.

你可以在[GitHub](https://github.com/JulianDan/mBlog)上获取其源代码.

## Markdown

素笔目前支持的MD语法有:

- Markdown基础语法
- 围栏代码块
- 表格
- 定义列表
- 删除线

## 添加文章

要添加文章，请在程序的运行目录下新建posts目录，并在posts目录中放置您的Markdown文件.

## 路由格式

文章的地址是其在文件系统中，在posts目录下的相对地址。例如，考虑以下目录结构：

```text
.
├── hidden
│   └── about.md
└── post.md
```

它会产生如下效果：

|  地址  | 文件 |
|---|---|
|  /hidden/about |  hidden/about.md |
|  /post |  post.md  |

## 主页与设置

主页会以文件的创建时间作为顺序，倒序排列你的所有文章。如果文章数大于*config.json*中*posts_per_page*的值，将会进行分页。 请求时，名为*page*的URL参数将控制页数.

博客的标题也可以在*config.json*中设置，它的键为*title*

此外，博客标题下面可以展示一些链接，便于跳转。它在*config.json*中的设置可以参考如下代码:

```json
{
  "links":{
    "主页":"/",
    "关于":"/about"
  }
}
```

## 一些小技巧

主页展示的文章不会递归扫描。换句话说，它只会扫描posts目录下的所有.md文件，而不会递归扫描其子目录。这样，如果你想让某篇文章可以被访问，但又不想使其出现在主页，你可以在posts目录下新建一个hidden目录，并将文章放置在其中。是不是很棒？
