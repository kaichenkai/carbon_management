# 快速开始指南 (Quick Start Guide)

## 方法一：使用自动化脚本 (Method 1: Using Setup Script)

### macOS/Linux

```bash
cd carbon_management
chmod +x setup.sh
./setup.sh
```

脚本会自动完成：
- 创建虚拟环境
- 安装依赖包
- 执行数据库迁移
- 创建超级管理员

### Windows

```bash
cd carbon_management
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

## 方法二：手动安装 (Method 2: Manual Installation)

### 1. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate  # Windows
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 数据库迁移

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. 创建超级管理员

```bash
python manage.py createsuperuser
```

按提示输入：
- 用户名 (Username)
- 邮箱 (Email) - 可选
- 密码 (Password)

### 5. 运行开发服务器

```bash
python manage.py runserver
```

## 初始化数据

### 1. 访问管理后台

打开浏览器访问: http://127.0.0.1:8000/admin/

使用刚创建的超级管理员账号登录。

### 2. 创建酒店

在管理后台点击 "Hotels" → "Add Hotel"

填写信息：
- **酒店代码 (Hotel Code)**: HOTEL001
- **酒店名称 (Hotel Name)**: 示例酒店
- **酒店名称(英文) (Hotel Name EN)**: Sample Hotel
- **是否启用 (Is Active)**: ✓

点击 "Save"

### 3. 配置超级管理员账号

在管理后台点击 "Custom users" → 找到你的超级管理员账号 → 点击编辑

设置：
- **所属酒店 (Hotel)**: 选择刚创建的酒店
- **是否审批通过 (Is Approved)**: ✓
- **可管理系数 (Can Manage Coefficients)**: ✓

点击 "Save"

### 4. 访问系统

打开浏览器访问: http://127.0.0.1:8000/

使用超级管理员账号登录：
- 选择酒店代码
- 输入用户名
- 输入密码
- 点击登录

## 导入示例数据

### 1. 下载导入模板

登录系统后，进入 "系数管理" 页面，点击 "下载模板"

### 2. 填写数据

在Excel模板中填写示例数据：

| 产品编号 | 一级分类 | 二级分类 | 产品名称 | 产品名称(英文) | 单位 | 碳排放系数 | 特殊备注 |
|---------|---------|---------|---------|---------------|------|-----------|---------|
| F101000965 | Seafood | Molluscs, other | 石鳖 | Chiton | KG | 7.30 | |
| F101005265 | Meat | Bovine meat | 牛肉末 | Ground Beef | KG | 42.80 | |
| F101002059 | Meat | Pig meat | 培根 | Bacon | KG | 7.28 | |

### 3. 导入数据

在 "系数管理" 页面，点击 "批量导入"，选择填写好的Excel文件，点击 "开始导入"

## 常见问题

### Q: 无法登录？
A: 确保：
1. 用户的 "是否审批通过" 已勾选
2. 已选择正确的酒店代码
3. 用户名和密码正确

### Q: 看不到 "系数管理" 菜单？
A: 确保用户的 "可管理系数" 权限已勾选

### Q: 导入失败？
A: 检查：
1. Excel格式是否正确（.xlsx 或 .xls）
2. 必填字段是否都已填写
3. 碳排放系数是否为数字

### Q: 如何切换语言？
A: 点击页面右上角的 "中文" 或 "EN" 按钮

## 端口被占用？

如果8000端口被占用，可以指定其他端口：

```bash
python manage.py runserver 8080
```

然后访问 http://127.0.0.1:8080/

## 停止服务器

在终端按 `Ctrl + C`

## 下一步

- 创建更多用户和酒店
- 导入完整的系数数据
- 开始使用系统进行碳排放管理

详细文档请参考 [README.md](README.md)
