"""
网页抓取服务
负责从 URL 提取网页内容
"""

import httpx
import re
import json
from typing import Optional, Dict
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

# 尝试导入 trafilatura（更好的内容提取）
try:
    import trafilatura
    HAS_TRAFILATURA = True
except ImportError:
    HAS_TRAFILATURA = False


class WebScraper:
    """网页抓取器"""
    
    # 常见的广告/导航类元素选择器
    NOISE_SELECTORS = [
        'script', 'style', 'noscript', 'iframe',
        'nav', 'footer', 'header', 'aside',
        '.advertisement', '.ads', '.sidebar',
        '#comments', '.comment', '.nav', '.menu',
        '.social-share', '.related-posts'
    ]
    
    # 请求头
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }
    
    # X/Twitter 相关的域名模式
    TWITTER_DOMAINS = ['twitter.com', 'x.com', 'mobile.twitter.com', 'mobile.x.com']
    
    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
    
    def _is_twitter_url(self, url: str) -> bool:
        """检查是否是 X/Twitter 链接"""
        parsed = urlparse(url)
        return any(domain in parsed.netloc for domain in self.TWITTER_DOMAINS)
    
    def _extract_tweet_id(self, url: str) -> Optional[str]:
        """从 URL 提取推文 ID"""
        # 匹配 /status/123456789 格式
        match = re.search(r'/status/(\d+)', url)
        return match.group(1) if match else None
    
    def _extract_username(self, url: str) -> Optional[str]:
        """从 URL 提取用户名"""
        # 匹配 twitter.com/username 或 x.com/username
        match = re.search(r'(?:twitter\.com|x\.com)/([^/\?]+)', url)
        if match:
            username = match.group(1)
            # 排除特殊路径
            if username not in ['home', 'search', 'explore', 'notifications', 'messages', 'i', 'settings']:
                return username
        return None
    
    async def _fetch_twitter_content(self, url: str) -> Dict[str, Optional[str]]:
        """
        处理 X/Twitter 链接
        由于 Twitter 需要登录和 JavaScript，直接返回提示信息
        """
        tweet_id = self._extract_tweet_id(url)
        username = self._extract_username(url)
        
        # 构建友好的标题
        if username and tweet_id:
            title = f"@{username} 的推文"
        else:
            title = "X/Twitter 推文"
        
        # 返回提示信息，引导用户手动输入
        return {
            'title': title,
            'content': None,  # 内容为空，用户需要手动输入
            'description': f"推文链接: {url}",
            'error': None,  # 不返回错误，这是预期行为
            'twitter_hint': True  # 标记这是 Twitter 链接，前端可以显示特殊提示
        }
    
    async def fetch(self, url: str) -> Dict[str, Optional[str]]:
        """
        抓取网页内容
        
        Args:
            url: 网页 URL
        
        Returns:
            包含 title, content, description 的字典
        """
        # 特殊处理 X/Twitter 链接
        if self._is_twitter_url(url):
            return await self._fetch_twitter_content(url)
        
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                headers=self.HEADERS
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                html = response.text
        except Exception as e:
            return {
                'title': None,
                'content': None,
                'description': None,
                'error': str(e)
            }
        
        # 优先使用 trafilatura（内容提取效果更好）
        if HAS_TRAFILATURA:
            return self._extract_with_trafilatura(html, url)
        else:
            return self._extract_with_beautifulsoup(html, url)
    
    def _extract_with_trafilatura(self, html: str, url: str) -> Dict[str, Optional[str]]:
        """使用 trafilatura 提取内容"""
        # 提取主要内容
        content = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=True,
            include_links=False,
            output_format='txt'
        )
        
        # 提取元数据
        metadata = trafilatura.extract_metadata(html)
        
        title = None
        description = None
        
        if metadata:
            title = metadata.title
            description = metadata.description
        
        # 如果没有获取到标题，用 BeautifulSoup 再试试
        if not title:
            soup = BeautifulSoup(html, 'html.parser')
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text().strip()
        
        return {
            'title': title or self._extract_title_from_url(url),
            'content': content,
            'description': description,
            'error': None
        }
    
    def _extract_with_beautifulsoup(self, html: str, url: str) -> Dict[str, Optional[str]]:
        """使用 BeautifulSoup 提取内容"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # 提取标题
        title = None
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text().strip()
        
        # 提取描述
        description = None
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            description = meta_desc.get('content', '').strip()
        
        # 移除噪音元素
        for selector in self.NOISE_SELECTORS:
            for element in soup.select(selector):
                element.decompose()
        
        # 提取正文内容
        # 优先查找常见的文章容器
        article_selectors = [
            'article', 'main', '.article', '.post', '.content',
            '.article-content', '.post-content', '.entry-content',
            '#article', '#content', '#main-content'
        ]
        
        content = None
        for selector in article_selectors:
            container = soup.select_one(selector)
            if container:
                content = container.get_text(separator='\n', strip=True)
                if len(content) > 100:  # 内容足够长才使用
                    break
        
        # 如果没找到文章容器，使用 body
        if not content or len(content) < 100:
            body = soup.find('body')
            if body:
                content = body.get_text(separator='\n', strip=True)
        
        # 清理内容
        if content:
            content = self._clean_content(content)
        
        return {
            'title': title or self._extract_title_from_url(url),
            'content': content,
            'description': description,
            'error': None
        }
    
    def _clean_content(self, text: str) -> str:
        """清理提取的内容"""
        # 移除多余空行
        text = re.sub(r'\n{3,}', '\n\n', text)
        # 移除行首尾空白
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        # 移除过短的行（可能是菜单、按钮等）
        lines = [line for line in text.split('\n') if len(line) > 2 or line == '']
        return '\n'.join(lines)
    
    def _extract_title_from_url(self, url: str) -> str:
        """从 URL 提取标题"""
        parsed = urlparse(url)
        # 使用路径最后一部分作为标题
        path = parsed.path.rstrip('/')
        if path:
            title = path.split('/')[-1]
            # 移除扩展名
            title = re.sub(r'\.[a-z]+$', '', title, flags=re.IGNORECASE)
            # 替换连字符和下划线
            title = title.replace('-', ' ').replace('_', ' ')
            if title:
                return title.title()
        return parsed.netloc
    
    def extract_domain(self, url: str) -> str:
        """提取域名"""
        parsed = urlparse(url)
        return parsed.netloc
