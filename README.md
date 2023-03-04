# mBlog

一个类似于BearBlog的轻量博客框架，不过可以自行托管。

使用和BearBlog相同的CSS，简洁的同时也很美观。

最大的特点是“轻”，主页和文章页面的模板文件均在2KB左右。

使用Python Flask构建，用markdown库进行渲染。

目前支持的MD语法有:

- Markdown基础语法
- 围栏代码块
- 表格
- 定义列表
- 删除线

使用方法：将md文件放入运行目录下的posts目录，文件名将会被Flask作为路由地址。如`/demo`对应`posts/demo.md`文件

提示：如果在Markdown文件的第一行添加一行HTML注释(如`<!-- mBlog Demo -->`)，mBlog将会把注释的内容作为文章标题，否则将使用文件名作为标题。
