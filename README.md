# carbon_management
# 碳排放管理系统 (Carbon Emission Management System)

一个基于Django的碳排放管理系统，支持多酒店管理、系数库维护、数据录入和分析。

## 功能特点

### 1. 登录系统
- 酒店代码选择（多酒店支持）
- 用户名密码登录
- 记住我功能
- 中英文双语切换
- 用户审批机制

### 2. 系数管理
- 碳排放系数库的增删改查
- 二级分类管理（一级分类 → 二级分类）
- 批量导入导出（Excel格式）
- 智能搜索功能
- 权限控制（仅授权用户可管理）

### 3. 数据看板
- 用户信息展示
- 系统功能导航
- 使用说明

## 技术栈

- **框架**: Django 4.2 (LTS)
- **数据库**: SQLite3
- **前端**: Bootstrap 5 + Bootstrap Icons
- **国际化**: Django i18n (中文/英文)
- **Excel处理**: openpyxl

## 安装步骤

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

按提示输入用户名、邮箱和密码。

### 5. 编译翻译文件

```bash
python manage.py compilemessages
```

### 6. 运行开发服务器

```bash
python manage.py runserver
```

访问 http://127.0.0.1:8000/

## 初始化数据

### 1. 创建酒店

进入Django管理后台 http://127.0.0.1:8000/admin/

创建至少一个酒店记录：
- 酒店代码：例如 HOTEL001
- 酒店名称：例如 示例酒店
- 酒店名称(英文)：例如 Sample Hotel

### 2. 创建用户

在管理后台创建用户，并设置：
- 所属酒店
- 岗位
- 是否审批通过：勾选
- 可管理系数：勾选（如果需要管理系数库）

### 3. 导入系数数据

1. 登录系统
2. 进入"系数管理"页面
3. 点击"下载模板"
4. 填写系数数据
5. 点击"批量导入"上传文件

## 系数匹配逻辑

系统在数据录入时会自动执行以下匹配：

1. **第一步**：尝试产品代码精确匹配
2. **第二步**：尝试通过产品名称关键词匹配二级分类
3. **第三步**：无法匹配时标记为待处理

示例代码：
```python
def find_emission_factor(product_code, product_name):
    # 第一步：尝试产品代码精确匹配
    if product_code in product_code_mapping:
        category = product_code_mapping[product_code]
        return get_coefficient_by_category(category)
    
    # 第二步：尝试通过产品名称关键词匹配二级分类
    matched_category = keyword_match(product_name)
    if matched_category:
        return get_coefficient_by_category(matched_category)
    
    # 第三步：无法匹配，标记为待处理
    return None
```

## 权限说明

### 普通用户
- 登录系统
- 查看数据看板
- 录入和查看数据（待开发）

### 系数管理员
- 普通用户的所有权限
- 管理碳排放系数库
- 批量导入导出系数

### 超级管理员
- 所有权限
- Django管理后台访问
- 用户和酒店管理

## 目录结构

```
carbon_management/
├── carbon_management/          # 项目配置
│   ├── settings.py            # 设置文件
│   ├── urls.py                # URL配置
│   └── wsgi.py                # WSGI配置
├── coefficients/              # 系数管理应用
│   ├── models.py              # 数据模型
│   ├── views.py               # 视图函数
│   ├── forms.py               # 表单
│   ├── admin.py               # 管理后台
│   └── urls.py                # URL路由
├── templates/                 # 模板文件
│   ├── base.html              # 基础模板
│   └── coefficients/          # 系数管理应用模板
│       ├── login.html         # 登录页面
│       ├── dashboard.html     # 数据看板
│       ├── coefficient_list.html
│       ├── coefficient_form.html
│       └── ...
├── locale/                    # 国际化文件
├── static/                    # 静态文件
├── media/                     # 媒体文件
├── manage.py                  # Django管理脚本
├── requirements.txt           # 依赖包
└── README.md                  # 说明文档
```

## 数据模型

### Hotel (酒店)
- code: 酒店代码
- name: 酒店名称
- name_en: 酒店名称(英文)
- is_active: 是否启用

### CustomUser (用户)
- username: 用户名
- hotel: 所属酒店
- position: 岗位
- is_approved: 是否审批通过
- can_manage_coefficients: 可管理系数

### EmissionCategory (排放分类)
- name: 分类名称
- level: 分类级别 (1或2)
- parent: 父级分类

### EmissionCoefficient (碳排放系数)
- product_code: 产品编号
- category_level1: 一级分类
- category_level2: 二级分类
- product_name: 产品名称
- unit: 单位
- coefficient: 碳排放系数
- special_note: 特殊备注

## 国际化

系统支持中文和英文两种语言。

### 切换语言
在页面右上角点击"中文"或"EN"按钮即可切换语言。

### 添加新的翻译
1. 在代码中使用 `{% trans "文本" %}` 或 `_("文本")`
2. 运行 `python manage.py makemessages -l zh_Hans`
3. 编辑 `locale/zh_Hans/LC_MESSAGES/django.po`
4. 运行 `python manage.py compilemessages`

## 导入导出格式

### Excel模板格式

| 产品编号 | 一级分类 | 二级分类 | 产品名称 | 产品名称(英文) | 单位 | 碳排放系数 | 特殊备注 |
|---------|---------|---------|---------|---------------|------|-----------|---------|
| F101000965 | Seafood | Molluscs, other | Chiton（石鳖） | Chiton | KG | 7.30 | |
| F101005265 | Meat | Bovine meat | Ground Beef（牛肉末） | Ground Beef | KG | 42.80 | |

## 开发计划

- [x] 登录系统
- [x] 系数管理
- [x] 批量导入导出
- [ ] 数据录入页面
- [ ] 自动匹配功能
- [ ] 数据分析和报表
- [ ] 图表可视化

## 注意事项

1. **生产环境部署**：
   - 修改 `settings.py` 中的 `SECRET_KEY`
   - 设置 `DEBUG = False`
   - 配置 `ALLOWED_HOSTS`
   - 使用生产级数据库（PostgreSQL/MySQL）
   - 配置静态文件服务

2. **安全性**：
   - 定期更新依赖包
   - 使用强密码
   - 启用HTTPS
   - 配置CSRF保护

3. **性能优化**：
   - 使用数据库索引
   - 启用缓存
   - 优化查询

## 许可证

MIT License

## 联系方式

如有问题或建议，请联系开发团队。
>>>>>>> a61eeab (Initial commit)
