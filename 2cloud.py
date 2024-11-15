import json
import os

def process_json_file(input_file):
    # 获取输入文件的基础名称（不含扩展名）
    base_name = os.path.splitext(input_file)[0]
    output_file = f"{base_name}_encod.json"
    
    # 创建 res 文件夹（如果不存在）
    if not os.path.exists('res'):
        os.makedirs('res')
    
    # 读取原始 JSON 文件
    with open(input_file, 'r', encoding='utf-8') as f:
        data = f.read()
    
    # 去掉开头和结尾的大括号
    data = data.strip()[1:-1]
    
    # 分割对象并去除逗号
    objects = data.split('},')
    processed_objects = [obj.strip() + '}' for obj in objects[:-1]]
    processed_objects.append(objects[-1].strip())  # 最后一个对象可能已经有结束括号
    
    # 将处理后的对象写入新文件
    output_path = os.path.join('res', output_file)
    with open(output_path, 'w', encoding='utf-8') as f:
        for obj in processed_objects:
            f.write(obj + '\n')  # 每个对象写入一行
    
    print(f"处理完成：{output_path}")

def main():
    # 获取当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 查找当前目录下的所有 json 文件
    json_files = [f for f in os.listdir(current_dir) if f.endswith('.json')]
    
    if not json_files:
        print("当前目录下没有找到 JSON 文件")
        return
    
    # 处理每个找到的 JSON 文件
    for json_file in json_files:
        try:
            process_json_file(json_file)
        except Exception as e:
            print(f"处理文件 {json_file} 时出错：{str(e)}")

if __name__ == '__main__':
    main()
