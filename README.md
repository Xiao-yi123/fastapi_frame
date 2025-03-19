# 仓库描述
基于FastAPi库写的一个框架(此为示例版本)


# 应该目录
## 单应用模式
```markdown
|____app        应用目录
| |____routers      路由定义目录(__init__.py 文件必须)
| |____database     数据库目录
| | |____models.py      数据库Model文件
| | |____schemas.py     数据库Schemas文件
| | |____curd       数据库操作操作目录(__init__.py 文件必须)
| |____types        类型目录
| | |____response       响应类型目录(__init__.py 文件必须)
| | |____Enum           枚举类型目录(__init__.py 文件必须)
| | |____request        请求类型目录(__init__.py 文件必须)
| |____utils        工具目录(__init__.py 文件必须)
| |____logs         日志目录(__init__.py 文件必须)
| |____controllers      控制器目录(__init__.py 文件必须)
|____config     配置目录
| |____bgtask.py        后台任务文件
| |____database.py      数据库文件
| |____rabbitmq.py      MQ类文件
| |____dependency.py    依赖类文件
| |____settings.py      设置文件
| |____exceptions.py    异常类文件
| |____middleware.py    中间件文件
|____lib        核心文件目录
|____static     静态文件目录
| |____manage       管理目录
| | |____ConstantRoutes.json
| | |____UserRoutes.json
| | |____allowed_ips.txt    IP黑名单文件
|____.gitignore         git忽略文件
|____.version   Python版本文件
|____.example.env       环境变量示例文件
|____usage_skills.md    一些使用技巧文件
|____README.md          README 文件
|____main.py        运行文件
|____requirements.txt   指定项目依赖项文件
```

# 使用方法
## 创建并激活 python 虚拟环境
```shell
    python -m venv venv
   
    macos & linux 激活虚拟环境
    source venv/bin/activate

    windows 激活虚拟环境
    venv\Scripts\activate
```

## 安装依赖
```markdown
pip install -r requirements.txt
```
## 运行项目
```markdown
命令运行方式1
    python main.py

命令运行方式2
   gunicorn -k uvicorn.workers.UvicornWorker -c gunicorn_config.py main:app

使用gunicorn服务器运行
    gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 main:app
```

### 退出venv

   ```shell
   deactivate
   ```

### 异常处理
#### 进程占用
```angular2html
Linux
ps aux | grep gunicorn
kill -9 <PID>
kill -TERM ppid 关闭父进程以及相关子进程
kill -9 $(ps -ef | pgrep gunicorn)   杀死批量里程

windows
netstat -ano|findstr <PID>
taskkill | findstr "<PID>"
```

## 免责声明
<div id="disclaimer"> 

### 1. 项目目的与性质
本项目（以下简称“本项目”）是作为一个技术研究与学习工具而创建的，旨在探索和学习网络数据采集技术。本项目专注于自媒体平台的数据爬取技术研究，旨在提供给学习者和研究者作为技术交流之用。

### 2. 法律合规性声明
本项目开发者（以下简称“开发者”）郑重提醒用户在下载、安装和使用本项目时，严格遵守中华人民共和国相关法律法规，包括但不限于《中华人民共和国网络安全法》、《中华人民共和国反间谍法》等所有适用的国家法律和政策。用户应自行承担一切因使用本项目而可能引起的法律责任。

### 3. 使用目的限制
本项目严禁用于任何非法目的或非学习、非研究的商业行为。本项目不得用于任何形式的非法侵入他人计算机系统，不得用于任何侵犯他人知识产权或其他合法权益的行为。用户应保证其使用本项目的目的纯属个人学习和技术研究，不得用于任何形式的非法活动。

### 4. 免责声明
开发者已尽最大努力确保本项目的正当性及安全性，但不对用户使用本项目可能引起的任何形式的直接或间接损失承担责任。包括但不限于由于使用本项目而导致的任何数据丢失、设备损坏、法律诉讼等。

### 5. 知识产权声明
本项目的知识产权归开发者所有。本项目受到著作权法和国际著作权条约以及其他知识产权法律和条约的保护。用户在遵守本声明及相关法律法规的前提下，可以下载和使用本项目。

### 6. 最终解释权
关于本项目的最终解释权归开发者所有。开发者保留随时更改或更新本免责声明的权利，恕不另行通知。
</div>

