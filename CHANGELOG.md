# 更新日志 (Changelog)

## [2025-10-20] - 应用重命名

### 变更
- 将 `core` 应用重命名为 `coefficients`（系数管理）
- 更新了所有相关配置和引用

### 原因
- `core` 名称过于通用，不够明确
- `coefficients` 更准确地描述了该应用的功能（系数管理）
- 便于后续添加其他功能应用，如：
  - `data_entry` - 数据录入
  - `analytics` - 数据分析
  - `reports` - 报表生成
  - `accounts` - 账户管理

### 修改的文件
1. **目录重命名**
   - `core/` → `coefficients/`
   - `templates/core/` → `templates/coefficients/`

2. **配置文件**
   - `settings.py`: 
     - `INSTALLED_APPS` 中的 `'core'` → `'coefficients'`
     - `AUTH_USER_MODEL` 从 `'core.CustomUser'` → `'coefficients.CustomUser'`
   - `urls.py`: URL include 从 `'core.urls'` → `'coefficients.urls'`

3. **应用配置**
   - `coefficients/apps.py`: 
     - 类名从 `CoreConfig` → `CoefficientsConfig`
     - `name` 从 `'core'` → `'coefficients'`
     - 添加 `verbose_name = '系数管理'`

4. **视图文件**
   - `coefficients/views.py`: 所有模板路径从 `'core/...'` → `'coefficients/...'`

5. **文档**
   - `README.md`: 更新目录结构说明

### 注意事项
如果你已经运行过数据库迁移，需要：

1. **删除旧数据库**（如果是测试环境）
   ```bash
   rm db.sqlite3
   rm -rf coefficients/migrations/0*.py
   ```

2. **重新创建迁移**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   python manage.py createsuperuser
   ```

3. **如果是生产环境**，需要手动修改数据库表名和外键引用，或者使用数据迁移脚本。

### 后续建议的应用结构

```
carbon_management/
├── coefficients/       # 系数管理（已完成）
├── data_entry/        # 数据录入（待开发）
├── analytics/         # 数据分析（待开发）
├── reports/           # 报表生成（待开发）
└── accounts/          # 账户管理（可选，或使用 coefficients 中的用户模型）
```
