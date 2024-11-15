import json
import os

def process_json_files():
    # 确保data和cloudData目录存在
    data_dir = 'data'
    cloud_dir = 'data/cloudData'
    if not os.path.exists(data_dir):
        print(f"目录 {data_dir} 不存在")
        return
    
    # 创建cloudData目录（如果不存在）
    if not os.path.exists(cloud_dir):
        os.makedirs(cloud_dir)

    # 遍历data目录下的所有文件
    for filename in os.listdir(data_dir):
        if filename.endswith('.json'):
            input_path = os.path.join(data_dir, filename)
            output_path = os.path.join(cloud_dir, f'processed_{filename}')
            
            try:
                # 读取JSON文件
                with open(input_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                
                # 去除首尾的方括号
                if content.startswith('[') and content.endswith(']'):
                    content = content[1:-1]
                
                # 写入新文件到cloudData目录
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"处理完成: {filename} -> cloudData/processed_{filename}")
                
            except Exception as e:
                print(f"处理文件 {filename} 时出错: {str(e)}")

if __name__ == '__main__':
    process_json_files()
