# 英语背单词挑战 - 30天计划

## 🎯 功能特点

- **30天挑战计划**：每天完成背单词任务，连续30天奖励200元
- **智能单词分配**：每天5个新词 + 20个复习词
- **错词反复复习**：答错的单词会加入复习队列，直到答对
- **进度统计**：实时显示学习进度和奖金累计
- **单用户系统**：适合个人使用

## 📦 安装部署

### 本地运行

```bash
# 1. 进入项目目录
cd vocabulary-app

# 2. 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Mac/Linux
# 或
venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 初始化数据库和创建管理员账户
python app.py
```

然后访问：
```
http://localhost:5000/init
```

管理员账户：
- 用户名：admin
- 密码：admin123

登录后请立即修改密码！

### 云端部署（Railway）

1. 将代码推送到GitHub
2. 访问 https://railway.app/
3. 点击 "New Project" → "Deploy from GitHub repo"
4. 选择你的仓库
5. Railway会自动检测Flask应用并部署

## 📚 导入单词

1. 登录后点击"导入单词"
2. 准备CSV格式的单词数据：
```
英文,中文,年级,单元
apple,苹果,七年级,Unit1
banana,香蕉,七年级,Unit1
```
3. 粘贴到文本框并点击"导入单词"

## 🎮 使用流程

1. **登录系统**
2. **导入单词**（首次使用）
3. **开始每日任务**：
   - 显示中文含义
   - 输入英文拼写
   - 答对进入下一个
   - 答错加入复习队列
4. **完成任务**后查看进度和奖金统计

## 📊 数据结构

### 数据库表

- **users**: 用户表
- **words**: 单词库
- **user_words**: 用户单词掌握情况
- **daily_tasks**: 每日任务记录
- **challenge_progress**: 30天挑战进度

### 奖金计算

- 完成30天挑战 = 200元
- 可累计多个周期的奖励
- 统计页面显示总奖金金额

## 🔧 技术栈

- **后端**: Flask (Python)
- **数据库**: SQLite
- **前端**: Jinja2模板 + Bootstrap 5
- **部署**: Railway（支持其他云平台）

## 📝 待优化功能

- [ ] 密码修改功能
- [ ] 单词导出功能
- [ ] 学习历史查询
- [ ] 多用户支持
- [ ] 移动端优化
- [ ] 语音发音功能

## 🤝 贡献

欢迎提出建议和改进！

## 📄 许可证

MIT License
