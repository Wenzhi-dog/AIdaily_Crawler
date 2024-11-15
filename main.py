import argparse
from datetime import datetime
from ai_news_crawler import AiNewsCrawler
from utils import setup_logging

def main():
    # 设置命令行参数
    parser = argparse.ArgumentParser(description='AI News Crawler')
    parser.add_argument('--date', type=str, help='Date to crawl (yyyy-mm-dd)',
                       default=datetime.now().strftime('%Y-%m-%d'))
    args = parser.parse_args()

    # 设置日志
    logger = setup_logging()
    
    try:
        # 初始化爬虫
        crawler = AiNewsCrawler(args.date)
        # 开始爬取
        crawler.run()
        logger.info(f"Crawling completed for date: {args.date}")
    except Exception as e:
        logger.error(f"Crawling failed: {str(e)}")
        raise

if __name__ == "__main__":
    main() 