### pip
```shell
   创建虚拟环境
   注意python 版本需要3.7+
   python -m venv venv
   
   安装依赖库
   pip3 install -r requirements.txt
   
   pip 导出依赖库
   pip freeze > requirements.txt
   
   pip 删除所有包
   pip uninstall -r requirements.txt -y
```

### 列出目录结构
```shell
    # Windows 
    tree /f > list.txt
    # macos & Linux    
    find . -print | sed -e 's;[^/]*/;|____;g;s;____|; |;g' > list.txt

```


### 生成表模型
```angular2html
# 默认安装
$ pip install sqlacodegen==1.4.51
# 也可以指定版本安装，本人体验的是最新版本
$ pip install sqlacodegen==3.0.0rc3

$ sqlacodegen mysql+pymysql://root:root@127.0.0.1:3306/test --outfile models.py
```