# Python脚本用于处理.tbl文件，去除每行末尾的'|'字符
 
# 定义源文件和目标文件的路径
input_file = r"E:\study\shujuku\tpch\C07311AE-0220-40C4-A369-AE837CC9BB9D-TPC-H-Tool\TPC-H V3.0.1\dbgen\supplier.tbl"
output_file = r"E:\study\shujuku\tpch\C07311AE-0220-40C4-A369-AE837CC9BB9D-TPC-H-Tool\TPC-H V3.0.1\dbgen\supplier.tbl"

# 读取输入文件并处理每一行
with open(input_file, "r") as f:
    lines = f.readlines()
 
processed_lines = []
for line in lines:
    # 去掉行末尾的"|"符号
    print(line)
    processed_line = line.rstrip("|\n")
    print(processed_line)
    processed_lines.append(processed_line + "\n")
 
# 将处理后的结果写入输出文件
with open(output_file, "w") as f:
    f.writelines(processed_lines)
 
 
 
# 打印处理后的结果