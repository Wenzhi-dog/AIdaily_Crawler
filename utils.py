import os
import logging
import json
import requests
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict
from requests.exceptions import RequestException, Timeout
import csv
import pandas as pd

def setup_logging():
    """设置日志配置"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"crawler_{datetime.now().strftime('%Y%m%d')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

def download_image(url: str, date: str, retries: int = 3) -> Optional[str]:
    """
    下载图片并返回本地路径
    
    Args:
        url: 图片URL
        date: 日期字符串(yyyy-mm-dd)
        retries: 重试次数
        
    Returns:
        str: 成功则返回本地文件路径，失败则返回None
    """
    logger = logging.getLogger(__name__)
    
    try:
        # 验证URL格式
        if not url.startswith(('http://', 'https://')):
            logger.error(f"Invalid image URL format: {url}")
            return None
            
        # 创建图片保存目录
        image_dir = Path("images") / date
        image_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成唯一文件名
        url_hash = hashlib.md5(url.encode()).hexdigest()
        file_extension = _get_file_extension(url)
        file_name = f"{url_hash}{file_extension}"
        file_path = image_dir / file_name
        
        # 如果文件已存在，直接返回路径
        if file_path.exists():
            logger.info(f"Image already exists: {file_path}")
            return str(file_path)
        
        # 下载图片
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        for i in range(retries):
            try:
                response = requests.get(url, headers=headers, timeout=10, stream=True)
                response.raise_for_status()
                
                # 验证内容类型
                content_type = response.headers.get('content-type', '')
                if not content_type.startswith('image/'):
                    logger.error(f"Invalid content type: {content_type} for URL: {url}")
                    return None
                
                # 获取文件大小
                file_size = int(response.headers.get('content-length', 0))
                if file_size > 10 * 1024 * 1024:  # 限制10MB
                    logger.error(f"Image too large ({file_size} bytes): {url}")
                    return None
                
                # 分块下载
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                logger.info(f"Successfully downloaded image: {url} -> {file_path}")
                return str(file_path)
                
            except Timeout:
                logger.warning(f"Download timeout ({i+1}/{retries}): {url}")
                if i == retries - 1:
                    return None
                    
            except RequestException as e:
                logger.warning(f"Download failed ({i+1}/{retries}): {url}, error: {str(e)}")
                if i == retries - 1:
                    return None
                    
            except Exception as e:
                logger.error(f"Unexpected error while downloading image: {url}, error: {str(e)}")
                return None
                
    except Exception as e:
        logger.error(f"Failed to download image from {url}: {str(e)}")
        return None

def _get_file_extension(url: str) -> str:
    """从URL或内容类型获取文件扩展名"""
    # 常见图片扩展名
    known_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    
    # 从URL中获取扩展名
    path = url.split('?')[0]  # 移除查询参数
    ext = os.path.splitext(path)[1].lower()
    
    if ext in known_extensions:
        return ext
    return '.jpg'  # 默认使用.jpg

def save_to_json(news_list, date):
    """保存新闻数据到JSON文件，保留已有数据"""
    # 确保 res/res 目录存在
    if not os.path.exists('res/res'):
        os.makedirs('res/res')
    
    output_path = f'res/res/sina_{date}.json'
    
    # 读取现有的JSON文件（如果存在）
    existing_news = []
    if os.path.exists(output_path):
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                existing_news = json.load(f)
            logging.info(f"从现有文件中读取到 {len(existing_news)} 条新闻")
        except Exception as e:
            logging.error(f"读取现有JSON文件失败: {str(e)}")
    
    # 使用URL作为唯一标识，合并现有数据和新数据
    url_to_news = {news['url']: news for news in existing_news}
    
    # 更新或添加新的新闻
    for news in news_list:
        # 确保 hasImage 和 isRecommend 是布尔类型
        news['hasImage'] = bool(news['hasImage'])
        news['isRecommend'] = bool(news['isRecommend'])
        url_to_news[news['url']] = news
    
    # 将合并后的数据转换为列表
    merged_news = list(url_to_news.values())
    
    # 保存合并后的数据
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(merged_news, f, ensure_ascii=False, indent=2)

def save_to_csv(news_list, date):
    """保存新闻数据到CSV文件，保留已有数据"""
    # 确保 res 目录存在
    if not os.path.exists('res'):
        os.makedirs('res')
    
    output_path = f'res/sina_{date}.csv'
    
    # 读取现有的CSV文件（如果存在）
    existing_news = []
    if os.path.exists(output_path):
        try:
            df_existing = pd.read_csv(output_path)
            # 将 hasImage 和 isRecommend 转换为布尔类型
            if 'hasImage' in df_existing.columns:
                df_existing['hasImage'] = df_existing['hasImage'].astype(bool)
            if 'isRecommend' in df_existing.columns:
                df_existing['isRecommend'] = df_existing['isRecommend'].astype(bool)
            existing_news = df_existing.to_dict('records')
        except Exception as e:
            logging.error(f"读取现有CSV文件失败: {str(e)}")
    
    # 合并现有数据和新数据
    url_to_news = {news['url']: news for news in existing_news}
    
    # 更新或添加新的新闻
    for news in news_list:
        # 确保 hasImage 和 isRecommend 是布尔类型
        news['hasImage'] = bool(news['hasImage'])
        news['isRecommend'] = bool(news['isRecommend'])
        url_to_news[news['url']] = news
    
    # 将合并后的数据转换为列表
    merged_news = list(url_to_news.values())
    
    # 保存合并后的数据
    df = pd.DataFrame(merged_news)
    
    # 确保这些列是布尔类型
    df['hasImage'] = df['hasImage'].astype(bool)
    df['isRecommend'] = df['isRecommend'].astype(bool)
    
    df.to_csv(output_path, index=False)