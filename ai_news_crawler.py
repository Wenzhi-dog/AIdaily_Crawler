import logging
import json
import hashlib
import requests
import time
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from requests.exceptions import RequestException, Timeout, TooManyRedirects
from utils import download_image, save_to_csv

class AiNewsCrawlerException(Exception):
    """自定义爬虫异常基类"""
    pass

class NetworkError(AiNewsCrawlerException):
    """网络相关错误"""
    pass

class ParseError(AiNewsCrawlerException):
    """解析相关错误"""
    pass

class AiNewsCrawler:
    def __init__(self, date: str):
        self.date = date
        self.logger = logging.getLogger(__name__)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.keywords = [
            'AI', '人工智能', '机器学习', '深度学习', '马斯克', 'OpenAI', 'ChatGPT', 'GPT', '大语言模型', 'LLM'
        ]
        self.processed_urls = set()
        self.request_interval = 1  # 请求间隔(秒)
        self.last_request_time = 0

    def run(self):
        """运行爬虫主程序"""
        all_news = []
        
        try:
            # 爬取新浪科技
            self.logger.info("开始爬取新浪科技新闻...")
            sina_news = self.crawl_sina()
            all_news.extend(sina_news)
            self.logger.info(f"新浪科技新闻爬取完成，获取{len(sina_news)}条新闻")
            
            # 保存结果
            if all_news:
                try:
                    save_to_csv(all_news, self.date)
                    self.logger.info(f"成功保存{len(all_news)}条新闻到CSV文件")
                except Exception as e:
                    self.logger.error(f"保存新闻数据失败: {str(e)}")
                    raise
            else:
                self.logger.warning("未找到符合条件的新闻")

        except Exception as e:
            self.logger.error(f"爬虫运行失败: {str(e)}")
            raise

    def _respect_rate_limit(self):
        """请求频率限制"""
        current_time = time.time()
        time_elapsed = current_time - self.last_request_time
        if time_elapsed < self.request_interval:
            time.sleep(self.request_interval - time_elapsed)
        self.last_request_time = time.time()

    def _make_request(self, url: str, retries: int = 3) -> Optional[requests.Response]:
        """发送HTTP请求并处理重试"""
        self._respect_rate_limit()
        
        for i in range(retries):
            try:
                response = requests.get(url, headers=self.headers, timeout=10)
                response.raise_for_status()
                return response
                
            except Timeout:
                self.logger.warning(f"请求超时 ({i+1}/{retries}): {url}")
                if i == retries - 1:
                    raise NetworkError(f"请求多次超时: {url}")
                
            except TooManyRedirects:
                self.logger.error(f"重定向次数过多: {url}")
                raise NetworkError(f"重定向错误: {url}")
                
            except RequestException as e:
                self.logger.warning(f"请求失败 ({i+1}/{retries}): {url}, 错误: {str(e)}")
                if i == retries - 1:
                    raise NetworkError(f"请求失败: {url}, 错误: {str(e)}")
                time.sleep(2 ** i)  # 指数退避
                
        return None

    def _validate_news_data(self, news: Dict) -> bool:
        """验证新闻数据完整性"""
        required_fields = ['title', 'content', 'createTime', 'url']
        return all(field in news and news[field] for field in required_fields)

    def _parse_sina_news(self, item) -> Optional[Dict]:
        """解析新浪新闻数据"""
        try:
            # 提取新闻URL
            url = item.get('href', '')
            if not url:
                return None
            
            # 确保URL是完整的
            if not url.startswith('http'):
                url = 'https:' + url if url.startswith('//') else 'https://tech.sina.com.cn' + url
            
            # 检查URL是否有效
            if not url.endswith(('.html', '.shtml')) or 'sina.com.cn' not in url:
                return None
            
            if url in self.processed_urls:
                return None
            
            # 获取新闻详情页
            try:
                response = self._make_request(url)
                if not response:
                    return None
                
                # 设置正确的编码
                response.encoding = 'utf-8'
                soup = BeautifulSoup(response.text, 'lxml')
                
                # 提取标题
                title = None
                title_selectors = [
                    'h1.main-title',
                    'h1[class*="article-title"]',
                    'h1[class*="main_title"]',
                    'div.article-header h1'
                ]
                for selector in title_selectors:
                    title_elem = soup.select_one(selector)
                    if title_elem:
                        title = title_elem.text.strip()
                        break
                
                if not title:
                    return None
                
                # 提取内容
                content = ''
                content_selectors = [
                    'div.article p',
                    'div[id="article"] p',
                    'div[class*="article-content"] p'
                ]
                for selector in content_selectors:
                    paragraphs = soup.select(selector)
                    if paragraphs:
                        # 将所有段落组合成内容
                        content = ''.join([f"<p>{p.get_text().strip()}</p>" for p in paragraphs if p.get_text().strip()])
                        break
                
                if not content:
                    return None
                
                # 检查是否为广告内容
                ad_indicators = [
                    '<p>产品答疑|网站律师|SINA English</p>',
                    '<p>Copyright © 1996-2024 SINA Corporation</p>',
                    '<p>All Rights Reserved 新浪公司 版权所有</p>'
                ]
                
                # 如果内容包含广告特征，直接返回None
                if any(indicator in content for indicator in ad_indicators):
                    self.logger.info(f"跳过广告内容: {url}")
                    return None
                
                # 提取日期
                date = None
                date_selectors = [
                    'span.date',
                    'div.date-source span.date',
                    'div[class*="article-info"] span.date',
                    'div[class*="article-info"] span[class*="time"]'
                ]
                for selector in date_selectors:
                    date_elem = soup.select_one(selector)
                    if date_elem:
                        date = date_elem.text.strip()
                        break
                
                if not date:
                    return None
                
                # 提取图片
                image_url = ''
                image_selectors = [
                    'div.img_wrapper img',
                    'div[class*="article-content"] img',
                    'div.article img'
                ]
                for selector in image_selectors:
                    images = soup.select(selector)
                    for img in images:
                        src = img.get('src', '')
                        if src and not src.endswith(('.gif', 'icon')):
                            image_url = src
                            if not image_url.startswith('http'):
                                image_url = 'https:' + image_url
                            break
                    if image_url:
                        break
                
                # 构建新闻数据
                news_data = {
                    '_id': hashlib.md5(url.encode()).hexdigest(),
                    'title': title,
                    'brief': BeautifulSoup(content, 'lxml').get_text()[:100] + '...',
                    'content': content,  # 现在content只包含格式化的段落
                    'createTime': date,
                    'url': url,
                    'imageUrl': image_url,
                    'isRecommend': False,
                    'hasImage': bool(image_url)  # 根据imageUrl是否存在来设置hasImage
                }
                
                if self._validate_news_data(news_data):
                    self.processed_urls.add(url)
                    return news_data
                
                return None

            except Exception as e:
                self.logger.error(f"解析新闻详情失败 {url}: {str(e)}")
                return None

        except Exception as e:
            self.logger.error(f"解析新闻失败: {str(e)}")
            return None

    def _normalize_date(self, date_str: str) -> str:
        """标准化日期格式"""
        try:
            # 处理常见的日期格式
            date_formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d %H:%M',
                '%Y年%m月%d日 %H:%M',
                '%Y年%m月%d日',
                '%Y-%m-%d',
                '%m月%d日 %H:%M',
                '%m月%d日'
            ]
            
            # 如果日期字符串只包含月日，添加当前年份
            if '年' not in date_str and '-' not in date_str:
                date_str = f"{datetime.now().year}年{date_str}"
            
            # 尝试不同的日期格式
            for date_format in date_formats:
                try:
                    date_obj = datetime.strptime(date_str.strip(), date_format)
                    # 如果格式只包含月日，使用当前年份
                    if date_format in ['%m月%d日 %H:%M', '%m月%d日']:
                        date_obj = date_obj.replace(year=datetime.now().year)
                    return date_obj.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            
            raise ValueError(f"无法解析日期格式: {date_str}")
            
        except Exception as e:
            self.logger.error(f"日期格式化失败: {str(e)}")
            return ""

    def _is_valid_news(self, news: Dict) -> bool:
        """验证新闻是否符合条件"""
        try:
            if not self._validate_news_data(news):
                return False

            # 标准化并检查日期
            news_date = self._normalize_date(news['createTime'])
            if not news_date:
                return False
            
            target_date = datetime.strptime(self.date, '%Y-%m-%d').date()
            news_date_obj = datetime.strptime(news_date, '%Y-%m-%d').date()
            
            if news_date_obj != target_date:
                return False

            # 检查关键词
            text = f"{news['title']} {news['content']}"
            if not any(keyword.lower() in text.lower() for keyword in self.keywords):
                return False

            return True
            
        except Exception as e:
            self.logger.error(f"验证新闻失败: {str(e)}")
            return False

    def crawl_sina(self) -> List[Dict]:
        """爬取新浪科技新闻"""
        news_list = []
        try:
            # 只爬取新浪科技首页
            base_url = "https://tech.sina.com.cn/"
            try:
                response = self._make_request(base_url)
                if not response:
                    return news_list
                
                # 设置正确的编码
                response.encoding = 'utf-8'
                soup = BeautifulSoup(response.text, 'lxml')
                
                # 获取新闻列表
                news_items = []
                
                # 定义所有可能包含新闻链接的选择器
                selectors = {
                    '.tech-news a': True,           # 科技新闻区域的链接
                    '.feed-card-item h2 a': True,   # 新闻卡片的标题链接
                    '.news-list a': True,           # 新闻列表的链接
                    '.main-list a': True,           # 主要新闻列表的链接
                    'article a': True,              # 文章区域的链接
                    '.seo_data_list a': True,       # SEO区域的链接
                }
                
                # 遍历所有选择器获取链接和标题
                for selector in selectors:
                    items = soup.select(selector)
                    for item in items:
                        # 检查链接是否存在
                        if not item.get('href'):
                            continue
                        
                        # 获取标题文本
                        title = item.get_text(strip=True)
                        if not title:
                            continue
                        
                        # 检查标题是否包含关键词
                        if any(keyword.lower() in title.lower() for keyword in self.keywords):
                            news_items.append(item)
                            self.logger.info(f"找到相关标题: {title}")
                
                self.logger.info(f"在新浪科技首页找到 {len(news_items)} 条相关新闻链接")
                
                # 处理每条新闻
                for item in news_items:
                    try:
                        news = self._parse_sina_news(item)
                        if news and self._is_valid_news(news):
                            # 检查是否已经存在相同的新闻(根据URL或标题)
                            if not any(existing['url'] == news['url'] for existing in news_list):
                                news_list.append(news)
                                self.logger.info(f"成功解析新: {news['title']}")
                    except Exception as e:
                        self.logger.error(f"处理新闻失败: {str(e)}")
                        continue

            except Exception as e:
                self.logger.error(f"处理新浪科技首页失败: {str(e)}")

        except Exception as e:
            self.logger.error(f"爬取新浪科技新闻失败: {str(e)}")

        return news_list

    def get_article_content(self, url):
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 根据不同网站的结构选择合适的内容选择器
            article_content = None
            
            # 对于常见新闻网站的内容提取
            if 'sina.com' in url:
                article_content = soup.find('div', class_='article')
            elif 'qq.com' in url:
                article_content = soup.find('div', class_='content-article')
            else:
                # 通用提取方案，查找可能包含文章内容的标签
                article_content = soup.find(['article', 'div.article', 'div.content'])
            
            if article_content:
                # 保留HTML标签，但清理不必要的属性
                for tag in article_content.find_all(True):
                    allowed_attrs = ['href', 'src']  # 允许保留的属性
                    attrs = dict(tag.attrs)
                    for attr in attrs:
                        if attr not in allowed_attrs:
                            del tag[attr]
                
                # 返回清理后的HTML内容
                return str(article_content)
            return "无法提取文章内容"
            
        except Exception as e:
            print(f"获取文章内容时出错: {str(e)}")
            return "获取内容失败"