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
    
    async def _fetch_twitter_via_fxtwitter(self, url: str) -> Dict[str, Optional[str]]:
        """
        使用 FxTwitter/FixupX API 获取推文内容
        FxTwitter 是一个免费的 Twitter 内容代理服务
        """
        tweet_id = self._extract_tweet_id(url)
        username = self._extract_username(url)
        
        if not tweet_id or not username:
            return {'title': None, 'content': None, 'description': None, 'error': '无法解析推文 ID'}
        
        # 使用 FxTwitter API
        api_url = f"https://api.fxtwitter.com/{username}/status/{tweet_id}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(api_url)
                
                if response.status_code == 200:
                    data = response.json()
                    tweet = data.get('tweet', {})
                    
                    author_name = tweet.get('author', {}).get('name', username)
                    author_handle = tweet.get('author', {}).get('screen_name', username)
                    text = tweet.get('text', '')
                    created_at = tweet.get('created_at', '')
                    
                    # 构建标题
                    title = f"{author_name} (@{author_handle}) 的推文"
                    
                    # 构建完整内容
                    content_parts = [text]
                    
                    # 添加日期信息
                    if created_at:
                        content_parts.append(f"\n发布时间: {created_at}")
                    
                    # 如果有媒体，添加媒体描述
                    media = tweet.get('media', {})
                    if media:
                        photos = media.get('photos', [])
                        videos = media.get('videos', [])
                        if photos:
                            content_parts.append(f"\n[包含 {len(photos)} 张图片]")
                        if videos:
                            content_parts.append(f"\n[包含 {len(videos)} 个视频]")
                    
                    return {
                        'title': title,
                        'content': '\n'.join(content_parts),
                        'description': text[:200] if text else None,
                        'error': None
                    }
                else:
                    # API 失败，尝试 Nitter
                    return await self._fetch_twitter_via_nitter(url, username, tweet_id)
                    
        except Exception as e:
            # 出错时尝试 Nitter 备用方案
            return await self._fetch_twitter_via_nitter(url, username, tweet_id)
    
    async def _fetch_twitter_via_nitter(self, original_url: str, username: str, tweet_id: str) -> Dict[str, Optional[str]]:
        """
        使用 Nitter 实例获取推文内容（备用方案）
        Nitter 是 Twitter 的开源前端，不需要 JavaScript
        """
        # 多个 Nitter 实例，按顺序尝试
        nitter_instances = [
            'nitter.net',
            'nitter.privacydev.net',
            'nitter.poast.org',
        ]
        
        for instance in nitter_instances:
            nitter_url = f"https://{instance}/{username}/status/{tweet_id}"
            
            try:
                async with httpx.AsyncClient(
                    timeout=15.0,
                    follow_redirects=True,
                    headers=self.HEADERS
                ) as client:
                    response = await client.get(nitter_url)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # 提取推文内容
                        tweet_content = soup.select_one('.tweet-content')
                        tweet_text = tweet_content.get_text(strip=True) if tweet_content else None
                        
                        # 提取用户名
                        fullname = soup.select_one('.fullname')
                        author_name = fullname.get_text(strip=True) if fullname else username
                        
                        if tweet_text:
                            return {
                                'title': f"{author_name} 的推文",
                                'content': tweet_text,
                                'description': tweet_text[:200] if tweet_text else None,
                                'error': None
                            }
            except:
                continue
        
        # 所有方案都失败
        return {
            'title': f"X 推文 - {tweet_id}",
            'content': None,
            'description': f"推文链接: {original_url}",
            'error': 'X/Twitter 内容需要登录或 JavaScript 才能访问。建议手动复制推文内容。'
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
            return await self._fetch_twitter_via_fxtwitter(url)
        
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
