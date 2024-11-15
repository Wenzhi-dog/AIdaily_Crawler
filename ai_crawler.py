import requests
from bs4 import BeautifulSoup
import pandas as pd
import argparse
from datetime import datetime
import os
import time
import random
import logging

class AICrawler:
    def __init__(self):
        # 使用新浪科技的新闻API
        self.base_url = "https://feed.mix.sina.com.cn/api/roll/get"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Referer": "https://tech.sina.com.cn/"
        }
        self.setup_logging()
        
    def setup_logging(self):
        """设置日志"""
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        log_file = f'logs/crawler_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        
        # 配置日志格式
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()  # 同时输出到控制台
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def get_news_links(self, date_str=None):
        """获取新闻链接列表"""
        try:
            self.logger.info(f"开始获取新闻链接")
            
            # API参数
            params = {
                "pageid": "372",           # 科技频道
                "lid": "2431",             # AI/科技子频道
                "num": 50,                 # 获取条数
                "page": 1,                 # 页码
                "callback": "",            # 不需要JSONP回调
            }
            
            response = requests.get(self.base_url, headers=self.headers, params=params)
            self.logger.info(f"响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.logger.debug(f"API响应数据: {data}")
                
                if "result" in data and "data" in data["result"]:
                    news_list = data["result"]["data"]
                    
                    # AI相关关键词列表
                    ai_keywords = [
                        'ai', 'artificial intelligence', '人工智能', 
                        '机器学习', 'machine learning', '深度学习',
                        'deep learning', '神经网络', 'neural network',
                        'chatgpt', 'gpt', '大模型', 'llm',
                        '智能机器人', '智能助手', '人工智能助手'
                    ]
                    
                    news_links = []
                    for news in news_list:
                        title = news.get("title", "").lower()
                        url = news.get("url", "")
                        
                        # 检查标题是否包含AI相关关键词
                        is_ai_related = any(keyword in title for keyword in ai_keywords)
                        
                        if is_ai_related:
                            news_links.append({
                                "title": news["title"],
                                "url": url,
                                "publish_time": news.get("publish_time", "")
                            })
                            self.logger.info(f"找到AI相关新闻: {news['title']}")
                    
                    self.logger.info(f"共找到 {len(news_links)} 条AI相关新闻链接")
                    return news_links
                else:
                    self.logger.error("API响应格式不正确")
                    return []
            else:
                self.logger.error(f"API请求失败: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"获取新闻链接失败: {str(e)}", exc_info=True)
            return []

    def get_news_content(self, url):
        """获取新闻内容和第一张图片"""
        try:
            self.logger.info(f"开始获取新闻内容 - {url}")
            response = requests.get(url, headers=self.headers)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 获取发布时间
            publish_time = ''
            time_element = soup.find('span', class_='date')
            if time_element:
                publish_time = time_element.text.strip()
                self.logger.debug(f"获取到发布时间: {publish_time}")
            
            # 获取新闻内容
            content = ''
            article = soup.find('div', class_='article')
            if article:
                paragraphs = article.find_all('p')
                content = '\n'.join([p.text.strip() for p in paragraphs])
                self.logger.debug(f"获取到内容长度: {len(content)} 字符")
            
            # 获取第一张图片
            image_url = None
            if article:
                img_tag = article.find('img')
                if img_tag:
                    image_url = img_tag.get('src')
                    if image_url and not image_url.startswith('http'):
                        image_url = 'https:' + image_url
                    self.logger.info(f"找到文章图片: {image_url}")
            
            return publish_time, content, image_url
        except Exception as e:
            self.logger.error(f"获取新闻内容失败 {url}: {str(e)}", exc_info=True)
            return '', '', None

    def save_image(self, image_url, title, date_str):
        """保存图片"""
        if not image_url:
            return None
        
        try:
            # 创建图片保存目录
            img_dir = os.path.join('data', 'images', date_str)
            os.makedirs(img_dir, exist_ok=True)
            
            # 生成安全的文件名
            safe_title = "".join(x for x in title if x.isalnum() or x in (' ', '-', '_')).rstrip()
            image_filename = f"{safe_title[:50]}.jpg"  # 限制文件名长度
            image_path = os.path.join(img_dir, image_filename)
            
            # 下载并保存图片
            response = requests.get(image_url, headers=self.headers)
            if response.status_code == 200:
                with open(image_path, 'wb') as f:
                    f.write(response.content)
                self.logger.info(f"图片已保存: {image_path}")
                return image_path
            else:
                self.logger.warning(f"图片下载失败: {image_url}")
                return None
            
        except Exception as e:
            self.logger.error(f"保存图片失败: {str(e)}", exc_info=True)
            return None

    def get_brief(self, content):
        """从新闻全文中提取第一句话作为简介"""
        if not content:
            return ""
        # 按句号、感叹号、问号分割，获取第一句话
        sentences = content.split('。')[0].split('！')[0].split('？')[0]
        return sentences.strip()

    def format_to_json(self, news_data):
        """将新闻数据转换为指定的JSON格式"""
        json_data = []
        for index, news in enumerate(news_data, 1):
            brief = self.get_brief(news['content'])
            
            # 处理日期格式
            create_time = datetime.now().strftime('%Y-%m-%d')  # 默认使用当前日期
            
            if news['publish_time']:
                try:
                    # 首先尝试直接提取日期部分（如果已经是标准格式）
                    if len(news['publish_time']) >= 10:
                        date_part = news['publish_time'][:10]
                        if '-' in date_part:  # 如果是类似 2024-11-14 的格式
                            create_time = date_part
                        else:
                            # 尝试其他格式
                            for fmt in ['%Y年%m月%d日', '%Y/%m/%d']:
                                try:
                                    date_obj = datetime.strptime(date_part, fmt)
                                    create_time = date_obj.strftime('%Y-%m-%d')
                                    break
                                except ValueError:
                                    continue
                except Exception as e:
                    self.logger.warning(f"日期解析失败: {e}, 使用当前日期")

            json_item = {
                "_id": str(index),
                "title": news['title'],
                "brief": brief,
                "content": news['content'],
                "createTime": create_time,
                "url": news['url'],
                "imageUrl": news.get('image_path', ''),  # 如果没有图片则为空字符串
                "isRecommend": False
            }
            json_data.append(json_item)
        return json_data

    def save_to_json(self, news_data, date_str):
        """保存数据为JSON格式"""
        if not os.path.exists('data'):
            os.makedirs('data')
            
        json_data = self.format_to_json(news_data)
        filename = f'data/ai_news_{date_str}.json'
        
        try:
            import json
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"数据已保存到: {filename}")
        except Exception as e:
            self.logger.error(f"保存JSON文件失败: {str(e)}")

    def crawl(self, date_str=None):
        """执行爬虫"""
        if not date_str:
            date_str = datetime.now().strftime('%Y-%m-%d')
            
        self.logger.info(f"开始爬取 {date_str} 的新闻")
        news_data = []
        news_links = self.get_news_links(date_str)
        
        for index, news in enumerate(news_links, 1):
            self.logger.info(f"正在爬取第 {index}/{len(news_links)} 条新闻")
            time.sleep(random.uniform(1, 3))  # 随机延时
            
            # 获取新闻内容、发布时间和图片
            publish_time = news.get('publish_time', '')
            _, content, image_url = self.get_news_content(news['url'])
            
            if not publish_time:
                publish_time, _, _ = self.get_news_content(news['url'])
            
            # 保存图片
            image_path = self.save_image(image_url, news['title'], date_str)
            
            news_data.append({
                'title': news['title'],
                'url': news['url'],
                'publish_time': publish_time,
                'content': content,
                'image_path': image_url if image_url else ''  # 使用原始图片URL而不是本地路径
            })
            self.logger.info(f"已爬取: {news['title']}")
        
        return news_data

def main():
    parser = argparse.ArgumentParser(description='AI新闻爬虫')
    parser.add_argument('--date', type=str, help='爬取指定日期的新闻 (YYYY-MM-DD格式)')
    args = parser.parse_args()

    crawler = AICrawler()
    date_str = args.date if args.date else datetime.now().strftime('%Y-%m-%d')
    
    crawler.logger.info(f"爬虫程序启动 - 目标日期: {date_str}")
    news_data = crawler.crawl(date_str)
    
    if news_data:
        crawler.save_to_json(news_data, date_str)  # 改用JSON格式保存
        crawler.logger.info(f"爬虫任务完成 - 共爬取 {len(news_data)} 条新闻")
    else:
        crawler.logger.warning("未找到相关新闻")

if __name__ == "__main__":
    main() 