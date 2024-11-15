# AI新闻爬虫

自动爬取新浪科技和网易新闻中的AI相关新闻。

## 功能特点

- 支持多个新闻源（新浪科技、网易新闻）
- 自动下载新闻图片
- 关键词过滤
- 日期筛选
- 完整的日志记录
- 支持定时任务

## 安装

```bash
pip install -r requirements.txt
```

## 使用方法

1. 单次爬取：
```bash
python main.py --date 2024-03-14
```

2. 启动定时任务：
```bash
python schedule_news_collector.py
```

## 输出

- 新闻数据保存在 `yyyy-mm-dd.json` 文件中
- 图片保存在 `images/yyyy-mm-dd/` 目录下
- 日志保存在 `logs/` 目录下 