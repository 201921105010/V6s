import os
import pytest
from bs4 import BeautifulSoup

def test_apple_style_css_rules():
    """验证苹果风格的大屏 UI 样式是否包含在 index.html 中"""
    html_path = os.path.join(
        os.path.dirname(__file__),
        "../views/warehouse_map_frontend/index.html"
    )
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, "html.parser")
    style_tag = soup.find("style")
    assert style_tag is not None, "缺少 style 标签"
    
    css_text = style_tag.string

    # 1. 验证 12-16px 圆角
    assert "border-radius: 16px;" in css_text or "border-radius: 12px;" in css_text, "未包含要求的卡片圆角样式"
    
    # 2. 验证柔和阴影
    assert "box-shadow:" in css_text and "rgba(0,0,0,0.05)" in css_text.replace(" ", ""), "未包含柔和阴影样式"
    
    # 3. 验证 5 等分格子
    assert "grid-template-rows: repeat(5, 1fr);" in css_text, "未包含 5 等分布局样式"
    
    # 4. 验证文字截断（两行换行、省略号、防溢出）
    assert "display: -webkit-box;" in css_text, "缺少 -webkit-box"
    assert "-webkit-line-clamp: 2;" in css_text, "未限制最多显示两行"
    assert "overflow: hidden;" in css_text, "未包含 overflow: hidden"
    assert "text-overflow: ellipsis;" in css_text, "未包含省略号截断"

    # 5. 验证响应式断点
    assert "@media (min-width: 1920px)" in css_text, "缺少 1920px 响应式断点"
    assert "@media (min-width: 2560px)" in css_text, "缺少 2560px 响应式断点"
    assert "@media (min-width: 3840px)" in css_text, "缺少 3840px 响应式断点"
