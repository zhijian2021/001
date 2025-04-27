import os
import requests
from bs4 import BeautifulSoup

# 目标网页和保存路径
base_url = "https://www.diancang.xyz/lishizhuanji/zizhitongjian/"
save_dir = "/home/s/Documents/资治通鉴"

# 批量下载 15004 到 15294
for idx in range(15294, 15295):
    url = f"{base_url}{idx}.html"
    try:
        response = requests.get(url, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')

        # 获取标题（h1标签）
        title_tag = soup.find('h1')
        title = title_tag.get_text(strip=True) if title_tag else f'无标题_{idx}'

        # 获取正文内容（id=content）
        content_tag = soup.find('div', id='content')
        if not content_tag:
            print(f"未找到正文内容区域: {url}")
            continue
        # 将<BR>换成换行符
        for br in content_tag.find_all('br'):
            br.replace_with('\n')
        content = content_tag.get_text('\n', strip=True)

        # 拼接保存内容
        save_text = f"{title}\n\n{content}"

        # 确保保存目录存在
        os.makedirs(save_dir, exist_ok=True)

        # 保存为txt文件
        save_path = os.path.join(save_dir, f"{title}.txt")
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(save_text)

        print(f"已保存到: {save_path}")
    except Exception as e:
        print(f"下载失败: {url}，原因: {e}") 