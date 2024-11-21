# AI 新闻爬虫

## 项目概述
该项目是一个用于从新浪科技网站提取与 AI 相关的新闻文章的网络爬虫工具。该工具根据特定关键词过滤新闻，并以 JSON 格式存储结果，同时下载相关图片。

## 功能
- **目标网站**：新浪科技
- **关键词过滤**：提取包含 AI 相关术语和 AI 领域知名人物的新闻文章。
- **日期指定**：抓取指定日期的新闻。
- **输出格式**：将结果存储为 JSON 文件，字段包括标题、内容和图片 URL。
- **日志记录**：将爬取过程和错误记录到文件中。

## 要求
- Python 3.x
- 所需的 Python 包列在 `requirements.txt` 中。

## 安装
1. 克隆仓库：
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```
2. 安装所需的包：
   ```bash
   pip install -r requirements.txt
   ```

## 使用
1. 运行爬虫：
   ```bash
   python main.py
   ```
   目前仅支持当日。

2. 结果将保存到 `res/res` 目录中，文件名为 `sina_yyyy-mm-dd.json`。

## 目录结构
```
/project-root/
  ├── main.py               # 主程序入口
  ├── ai_news_crawler.py    # 爬虫实现
  ├── utils.py              # 工具函数
  ├── config.py             # 配置文件
  ├── requirements.txt      # 项目依赖
  ├── images/               # 保存图片
  ├── logs/                 # 保存日志
  ├── res/                  # 保存爬取结果
  ├── README.md             # 项目文档
```

## 配置
- **关键词**：在 `config.py` 中定义，可以调整 `KEYWORDS` 和 `FILTER_KEYWORDS` 来自定义爬取条件。
- **图片下载超时**：在 `config.py` 中设置 `IMAGE_DOWNLOAD_TIMEOUT`。

## 日志
日志存储在 `logs` 目录中，每天运行爬虫时会创建一个新的日志文件。

## 未来功能
- **多日期支持**：允许用户指定多个日期进行新闻抓取。
- **多网站支持**：扩展爬虫以支持其他新闻网站。
- **自动化调度**：集成调度工具以定期自动运行爬虫。
- **数据分析**：增加对抓取数据的分析功能，如关键词趋势分析。
- **用户界面**：开发一个简单的用户界面以便于操作和查看结果。
- **多语言支持**：支持抓取和处理多语言新闻内容。