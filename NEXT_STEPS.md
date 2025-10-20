# 下一步操作指南

## ✅ 已完成
- Django项目创建
- 数据库迁移
- 超级管理员创建
- 登录页面优化（白色背景 + 树叶图标）
- 翻译文件创建

## ⚠️ 需要执行（重要）

### 1. 编译翻译文件（必须！）

```bash
cd /Users/kai/Desktop/practice/2025/10/08_Ruby/Ruby_code/carbon_management
python3 manage.py compilemessages
```

**这一步非常重要！** 不执行的话，中英文切换不会生效。

### 2. 创建酒店数据

```bash
python3 manage.py create_hotels
```

这将创建两个示例酒店：
- HOTEL001: 绿色环保酒店（北京）
- HOTEL002: 碳中和度假酒店（上海）

### 3. 配置超级管理员

1. 访问管理后台：http://127.0.0.1:8000/admin/
2. 登录（用户名：admin）
3. 点击 "Custom users" → 找到 admin 用户 → 点击编辑
4. 设置以下字段：
   - **所属酒店**：选择一个酒店（例如 HOTEL001）
   - **是否审批通过**：✓ 勾选
   - **可管理系数**：✓ 勾选
5. 点击保存

### 4. 重启服务器

```bash
python3 manage.py runserver
```

### 5. 测试登录

1. 访问：http://127.0.0.1:8000/
2. 选择酒店代码
3. 输入用户名：admin
4. 输入密码
5. 点击登录

## 🎨 当前效果

### 登录页面
- ✅ 白色背景（替代了紫色渐变）
- ✅ 树叶图标（绿色圆角方块）
- ✅ 标题：酒店碳排放管理平台
- ✅ 副标题：精准测算酒店碳排放，助力可持续经营
- ✅ 横向布局（图标在左，文字在右）
- ✅ 底部分隔线

### 语言切换
- 点击右上角 "中文" / "EN" 按钮
- 编译翻译文件后即可生效

## 📋 快速命令合集

```bash
# 进入项目目录
cd /Users/kai/Desktop/practice/2025/10/08_Ruby/Ruby_code/carbon_management

# 编译翻译（必须）
python3 manage.py compilemessages

# 创建酒店数据
python3 manage.py create_hotels

# 启动服务器
python3 manage.py runserver
```

## 🔍 验证清单

- [ ] 翻译文件已编译（.mo 文件存在）
- [ ] 酒店数据已创建
- [ ] 超级管理员已配置酒店和权限
- [ ] 可以正常登录
- [ ] 中英文切换正常工作
- [ ] 登录页面显示正确（白色背景 + 树叶图标）

## 📞 遇到问题？

### 问题1：中英文切换不生效
**解决方案**：运行 `python3 manage.py compilemessages`

### 问题2：登录时提示"账号未审批"
**解决方案**：在管理后台勾选用户的"是否审批通过"

### 问题3：登录后看不到"系数管理"菜单
**解决方案**：在管理后台勾选用户的"可管理系数"

### 问题4：酒店下拉框为空
**解决方案**：运行 `python3 manage.py create_hotels` 创建酒店数据
