import json
import os

def process_json_file(input_file):
    # 获取输入文件的基础名称（不含扩展名）
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    output_file = f"{base_name}_encod.json"
    
    # 创建 res/encode 文件夹（如果不存在）
    encode_dir = 'res/encode'
    if not os.path.exists(encode_dir):
        os.makedirs(encode_dir)
    
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
    output_path = os.path.join(encode_dir, output_file)
    with open(output_path, 'w', encoding='utf-8') as f:
        for obj in processed_objects:
            f.write(obj + '\n')  # 每个对象写入一行
    
    print(f"处理完成：{output_path}")

def main():
    # 指定输入目录
    input_dir = 'res/res'
    
    # 确保输入目录存在
    if not os.path.exists(input_dir):
        print(f"输入目录 {input_dir} 不存在")
        return
    
    # 查找 res/res 目录下的所有 json 文件
    json_files = [f for f in os.listdir(input_dir) if f.endswith('.json')]
    
    if not json_files:
        print(f"{input_dir} 目录下没有找到 JSON 文件")
        return
    
    # 处理每个找到的 JSON 文件
    for json_file in json_files:
        try:
            input_path = os.path.join(input_dir, json_file)
            process_json_file(input_path)
        except Exception as e:
            print(f"处理文件 {json_file} 时出错：{str(e)}")

if __name__ == '__main__':
    main()
