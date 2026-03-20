"""
测试大纲生成功能
"""
import sys
sys.path.insert(0, '/home/iecube_xiaolong/project/tutorial/backend')

from app.services.ai_service import AIService

def test_outline_generation():
    """测试大纲生成"""
    print("=" * 60)
    print("测试大纲生成功能")
    print("=" * 60)
    
    ai = AIService()
    
    if not ai.kimi_client:
        print("❌ Kimi API 未配置，请在 .env 文件中设置 KIMI_API_KEY")
        return
    
    print("✓ Kimi 客户端已初始化")
    
    # 测试大纲生成
    try:
        print("\n正在生成大纲...")
        outline = ai.generate_outline(
            course="Python 编程基础",
            knowledge_point="函数与模块",
            difficulty="easy"
        )
        
        print("✓ 大纲生成成功")
        print(f"\n大纲标题: {outline.get('title', 'N/A')}")
        print(f"描述: {outline.get('description', 'N/A')}")
        print(f"章节数: {len(outline.get('sections', []))}")
        
        # 显示章节结构
        print("\n章节结构:")
        for i, section in enumerate(outline.get('sections', []), 1):
            print(f"  {i}. {section.get('title', 'N/A')}")
            for j, sub in enumerate(section.get('subsections', []), 1):
                print(f"     {i}.{j} {sub.get('title', 'N/A')}")
        
        # 测试章节内容生成
        if outline.get('sections'):
            print("\n" + "=" * 60)
            print("测试章节内容生成")
            print("=" * 60)
            
            first_section = outline['sections'][0]
            print(f"\n正在生成章节内容: {first_section.get('title')}")
            
            html_content = ai.generate_section_content(first_section)
            print("✓ 章节内容生成成功")
            print(f"内容长度: {len(html_content)} 字符")
            print(f"\n内容预览 (前500字符):")
            print(html_content[:500] + "...")
    
    except Exception as e:
        print(f"❌ 测试失败: {e}")


if __name__ == "__main__":
    test_outline_generation()
